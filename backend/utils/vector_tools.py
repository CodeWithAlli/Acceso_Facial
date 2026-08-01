# backend/utils/vector_tools.py
"""
Extraccion y comparacion de rostros usando reconocimiento facial REAL
(YuNet para deteccion + SFace para el embedding de identidad).

Por que se cambio de MediaPipe Face Mesh a esto:
- Face Mesh entrega la posicion geometrica de 468 puntos TAL COMO
  aparece la cara en el frame (angulo, distancia a la camara, gesto).
  No es un embedding de identidad: la misma persona en dos angulos
  distintos puede dar similitud baja, y dos personas distintas
  centradas igual pueden dar similitud alta. Por eso el sistema podia
  fallar en uso real aunque en pruebas locales "pareciera" funcionar.
- SFace SI esta entrenado para identidad: el vector de 128 valores es
  estable ante cambios moderados de pose, iluminacion y expresion.

Rendimiento:
- El vector de cada usuario se calcula UNA SOLA VEZ al registrarse y
  se guarda en la columna `vector_facial` de la tabla `rostros`.
- La autenticacion ya NO vuelve a leer ni procesar imagenes de disco,
  solo compara los vectores guardados -> mucho mas rapido y liviano.
"""

import os
import json
import base64
import numpy as np
import cv2

from backend.config import config

MODELS_DIR      = os.path.join(os.path.dirname(__file__), '..', 'models')
DETECTOR_PATH   = os.path.join(MODELS_DIR, 'face_detection_yunet_2023mar.onnx')
RECOGNIZER_PATH = os.path.join(MODELS_DIR, 'face_recognition_sface_2021dec.onnx')

if not os.path.exists(DETECTOR_PATH) or not os.path.exists(RECOGNIZER_PATH):
    raise FileNotFoundError(
        'Faltan los modelos ONNX en backend/models/. '
        'Revisa el README, seccion "Descargar modelos de reconocimiento facial".'
    )

# Los modelos se cargan UNA vez al iniciar el proceso Flask, no en cada request.
_detector = cv2.FaceDetectorYN.create(
    DETECTOR_PATH, "", (320, 320),
    score_threshold=0.7, nms_threshold=0.3, top_k=5000
)
_recognizer = cv2.FaceRecognizerSF.create(RECOGNIZER_PATH, "")


def _detectar_y_alinear(img: np.ndarray):
    """Detecta el rostro principal (mayor confianza) y devuelve el recorte alineado 112x112."""
    h, w = img.shape[:2]
    _detector.setInputSize((w, h))
    _, caras = _detector.detect(img)
    if caras is None or len(caras) == 0:
        return None
    mejor = caras[np.argmax(caras[:, -1])]   # columna -1 = score de confianza
    return _recognizer.alignCrop(img, mejor)


def _vector_desde_imagen(img: np.ndarray):
    """Pipeline completo: deteccion -> alineacion -> embedding 128-d."""
    if img is None:
        return None
    rostro_alineado = _detectar_y_alinear(img)
    if rostro_alineado is None:
        return None
    feat = _recognizer.feature(rostro_alineado)
    return feat.flatten()


def extraer_vector(imagen_path: str):
    """Extrae el embedding facial desde un archivo de imagen en disco."""
    img = cv2.imread(imagen_path)
    return _vector_desde_imagen(img)


def vector_desde_base64(b64_string: str):
    """Extrae el embedding facial desde una imagen en base64 (la que manda el frontend)."""
    try:
        datos = base64.b64decode(b64_string.split(',')[-1])
        arr = np.frombuffer(datos, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return _vector_desde_imagen(img)
    except Exception as e:
        print(f'[VECTOR ERROR] {e}')
        return None


def vector_a_json(vector: np.ndarray) -> str:
    """Serializa el embedding para guardarlo en la columna vector_facial (TEXT)."""
    return json.dumps(vector.tolist())


def vector_desde_json(valor) -> np.ndarray:
    """
    Deserializa un embedding guardado en la BD.
    Postgres/Supabase (columna JSONB) ya devuelve el valor parseado
    (una lista de floats), mientras que un string JSON crudo tambien
    se acepta por si se usa con otra base de datos.
    """
    datos = json.loads(valor) if isinstance(valor, str) else valor
    return np.array(datos, dtype=np.float32)


def similitud_coseno(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Similitud coseno usando el comparador nativo de SFace.
    Rango real observado: ~0.0 (distinto) a ~1.0 (misma persona).
    OpenCV recomienda un umbral de referencia de 0.363 para SFace + coseno
    (ver config.SIMILARITY_THRESHOLD, ajustable segun tus pruebas).
    """
    v1 = v1.reshape(1, -1).astype(np.float32)
    v2 = v2.reshape(1, -1).astype(np.float32)
    return float(_recognizer.match(v1, v2, cv2.FaceRecognizerSF_FR_COSINE))


def encontrar_mejor_coincidencia(vector_actual, rostros_bd):
    """
    Compara vector_actual contra los embeddings YA GUARDADOS en BD.
    rostros_bd: lista de dicts con 'usuario_id', 'nombre', 'vector_facial' (JSON, string)
    Retorna (usuario_id, nombre, similitud) del mejor match, o (None, None, sim) si no supera el umbral.
    """
    mejor_sim = -1.0
    mejor_usuario = (None, None)
    for rostro in rostros_bd:
        if not rostro.get('vector_facial'):
            continue
        vec_bd = vector_desde_json(rostro['vector_facial'])
        sim = similitud_coseno(vector_actual, vec_bd)
        if sim > mejor_sim:
            mejor_sim = sim
            mejor_usuario = (rostro['usuario_id'], rostro['nombre'])
    if mejor_sim >= config.SIMILARITY_THRESHOLD:
        return mejor_usuario[0], mejor_usuario[1], mejor_sim
    return None, None, mejor_sim
