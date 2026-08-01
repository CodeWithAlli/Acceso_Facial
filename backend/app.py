# backend/app.py
# Servidor Flask - todos los endpoints REST del sistema de asistencia facial.
# Migrado a Supabase (Postgres). Logica de negocio: 1 ingreso + 1 salida por
# dia por persona, DNI para busqueda rapida del admin, justificaciones,
# panel de administrador con login por password o rostro.

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import os
import uuid
import base64
from datetime import datetime, date
import calendar

from backend.config import config
from backend.db import (
    crear_usuario, buscar_usuarios, listar_usuarios, obtener_usuario_por_id,
    guardar_rostro, obtener_rostros_todos,
    accesos_de_hoy, registrar_acceso, editar_acceso_manual, obtener_historial,
    crear_justificacion, listar_justificaciones,
    guardar_resumen_periodo, guardar_vector_facial_admin
)
from backend.utils.vector_tools import (
    vector_desde_base64, encontrar_mejor_coincidencia, vector_a_json
)
from backend.utils.voice import (
    audio_bienvenida, audio_despedida, audio_ya_registrado, audio_acceso_denegado
)
from backend.utils.storage_supabase import subir_archivo
from backend.auth import login_password, login_facial

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
jwt = JWTManager(app)

# Fotos y audio ya no se guardan en disco local (efimero en produccion):
# van directo a los buckets 'rostros' y 'audios' de Supabase Storage.


# ── UTILIDADES ───────────────────────────────────────────────────────────

def guardar_imagen_base64(b64: str) -> str:
    """Sube la foto al bucket 'rostros' de Supabase Storage y retorna su URL publica."""
    datos  = base64.b64decode(b64.split(',')[-1])
    nombre = f'{uuid.uuid4().hex}.jpg'
    return subir_archivo('rostros', nombre, datos, 'image/jpeg')


def _es_fuera_de_horario(usuario: dict, tipo_evento: str) -> bool:
    """Compara la hora actual contra el horario esperado del usuario (o el default)."""
    ahora = datetime.now().time()
    tolerancia = config.TOLERANCIA_MINUTOS

    if tipo_evento == 'ingreso':
        limite = usuario.get('hora_entrada_esperada') or datetime.strptime(config.HORA_ENTRADA_DEFAULT, '%H:%M').time()
        minutos_diferencia = (ahora.hour * 60 + ahora.minute) - (limite.hour * 60 + limite.minute)
        return minutos_diferencia > tolerancia
    else:  # salida
        limite = usuario.get('hora_salida_esperada') or datetime.strptime(config.HORA_SALIDA_DEFAULT, '%H:%M').time()
        minutos_diferencia = (limite.hour * 60 + limite.minute) - (ahora.hour * 60 + ahora.minute)
        return minutos_diferencia > tolerancia   # salio mas temprano de lo esperado


# ── USUARIOS ─────────────────────────────────────────────────────────────

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    return jsonify(listar_usuarios())


@app.route('/api/usuarios/<int:uid>', methods=['GET'])
def get_usuario(uid):
    usuario = obtener_usuario_por_id(uid)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404
    return jsonify(usuario)


@app.route('/api/personas', methods=['GET'])
@jwt_required()
def get_buscar_personas():
    """
    Busqueda para el dashboard del administrador: el dashboard evalua a UNA
    persona a la vez, no a todos. Busca por nombre completo o por DNI.
    Uso: GET /api/personas?buscar=Ana  o  GET /api/personas?buscar=45678912
    """
    termino = request.args.get('buscar', '').strip()
    if not termino:
        return jsonify({'error': 'Falta el parametro buscar'}), 400
    return jsonify(buscar_usuarios(termino))


# ── REGISTRO (alta de usuario + primer rostro) ───────────────────────────

@app.route('/api/registro', methods=['POST'])
def registro():
    """
    Recibe: { nombre_completo, dni, tipo_persona: 'empleado'|'estudiante', imagen_base64 }
    Crea el usuario, guarda la imagen y calcula + guarda el embedding facial
    UNA sola vez (no se vuelve a calcular en cada autenticacion futura).
    """
    data = request.get_json()
    nombre_completo = data.get('nombre_completo', '').strip()
    dni             = data.get('dni', '').strip()
    tipo_persona    = data.get('tipo_persona', '').strip()
    imagen          = data.get('imagen_base64', '')

    if not nombre_completo or not dni or not imagen:
        return jsonify({'error': 'nombre_completo, dni e imagen_base64 son requeridos'}), 400
    if tipo_persona not in ('empleado', 'estudiante'):
        return jsonify({'error': "tipo_persona debe ser 'empleado' o 'estudiante'"}), 400

    vector = vector_desde_base64(imagen)
    if vector is None:
        return jsonify({'error': 'No se detecto un rostro valido en la imagen'}), 400

    uid = crear_usuario(nombre_completo, dni, tipo_persona)
    if uid is None:
        return jsonify({'error': f'Ya existe una persona registrada con el DNI {dni}'}), 409

    ruta = guardar_imagen_base64(imagen)
    guardar_rostro(uid, ruta, vector_a_json(vector))

    return jsonify({
        'mensaje': f'{nombre_completo} registrado correctamente',
        'usuario_id': uid
    }), 201


# ── EVENTO DE ASISTENCIA (reemplaza /api/autenticar) ─────────────────────

@app.route('/api/evento', methods=['POST'])
def evento_asistencia():
    """
    Recibe: { imagen_base64 }
    Reconoce el rostro y decide AUTOMATICAMENTE si es ingreso o salida:
      - Si hoy no tiene ingreso registrado  -> registra ingreso.
      - Si ya tiene ingreso pero no salida  -> registra salida.
      - Si ya tiene ambos (ingreso Y salida de hoy) -> no inserta de nuevo,
        avisa que ya completo su asistencia del dia.
    """
    data   = request.get_json()
    imagen = data.get('imagen_base64', '')
    if not imagen:
        return jsonify({'error': 'imagen_base64 es requerida'}), 400

    vector = vector_desde_base64(imagen)
    if vector is None:
        return jsonify({'acceso': False, 'mensaje': 'Sin rostro detectado'}), 200

    rostros = obtener_rostros_todos()
    uid, nombre, sim = encontrar_mejor_coincidencia(vector, rostros)

    if uid is None:
        audio_path = audio_acceso_denegado()
        return jsonify({
            'acceso': False,
            'similitud': round(sim, 4),
            'mensaje': 'Rostro no reconocido',
            'audio_url': audio_path  # ya es una URL publica absoluta de Supabase Storage
        })

    usuario = obtener_usuario_por_id(uid)
    hoy = accesos_de_hoy(uid)

    if hoy['ingreso'] is None:
        fuera = _es_fuera_de_horario(usuario, 'ingreso')
        resultado = registrar_acceso(uid, 'ingreso', fuera)
        audio_path = audio_bienvenida(uid, nombre)
        return jsonify({
            'acceso': True, 'evento': 'ingreso', 'usuario_id': uid, 'nombre': nombre,
            'fuera_de_horario': fuera, 'similitud': round(sim, 4),
            'audio_url': audio_path  # ya es una URL publica absoluta de Supabase Storage
        })

    if hoy['salida'] is None:
        fuera = _es_fuera_de_horario(usuario, 'salida')
        resultado = registrar_acceso(uid, 'salida', fuera)
        audio_path = audio_despedida(uid, nombre)
        return jsonify({
            'acceso': True, 'evento': 'salida', 'usuario_id': uid, 'nombre': nombre,
            'fuera_de_horario': fuera, 'similitud': round(sim, 4),
            'audio_url': audio_path  # ya es una URL publica absoluta de Supabase Storage
        })

    # Ya tiene ingreso Y salida hoy: no se permite un tercer registro.
    audio_path = audio_ya_registrado(nombre)
    return jsonify({
        'acceso': True, 'evento': 'ya_completo', 'usuario_id': uid, 'nombre': nombre,
        'mensaje': f'{nombre} ya registro ingreso y salida hoy',
        'audio_url': audio_path  # ya es una URL publica absoluta de Supabase Storage
    })


# ── HISTORIAL ────────────────────────────────────────────────────────────

@app.route('/api/historial', methods=['GET'])
@jwt_required()
def historial():
    """
    GET /api/historial?limite=50            -> historial general
    GET /api/historial?usuario_id=3&limite=50 -> historial de una sola persona
    (el dashboard evalua a la persona buscada, no a todos a la vez)
    """
    limite     = request.args.get('limite', 50, type=int)
    usuario_id = request.args.get('usuario_id', type=int)
    datos = obtener_historial(usuario_id=usuario_id, limite=limite)
    for d in datos:
        if d.get('hora'):
            d['hora'] = str(d['hora'])
        if d.get('fecha'):
            d['fecha'] = str(d['fecha'])
    return jsonify(datos)


# ── JUSTIFICACIONES (requieren sesion de administrador) ──────────────────

@app.route('/api/justificaciones', methods=['POST'])
@jwt_required()
def post_justificacion():
    """
    Requiere header Authorization: Bearer <token>.
    Body: { usuario_id, fecha: 'YYYY-MM-DD', tipo: 'falta'|'tardanza'|'salida_temprana', motivo }
    Una falta/tardanza justificada no genera descuento ni queda como
    nota negativa en el resumen del periodo.
    """
    admin_id = int(get_jwt_identity())
    data = request.get_json()
    ok = crear_justificacion(
        data['usuario_id'], data['fecha'], data['tipo'], data['motivo'], admin_id
    )
    return jsonify({'mensaje': 'Justificacion guardada' if ok else 'Error al guardar'}), (201 if ok else 500)


@app.route('/api/justificaciones/<int:usuario_id>', methods=['GET'])
def get_justificaciones(usuario_id):
    desde = request.args.get('desde')
    hasta = request.args.get('hasta')
    return jsonify(listar_justificaciones(usuario_id, desde, hasta))


# ── EDICION MANUAL DE UN REGISTRO (requiere admin) ───────────────────────

@app.route('/api/accesos/<int:acceso_id>', methods=['PUT'])
@jwt_required()
def put_acceso(acceso_id):
    admin_id = int(get_jwt_identity())
    data = request.get_json()
    ok = editar_acceso_manual(acceso_id, data['hora'], admin_id)
    if not ok:
        return jsonify({'error': 'Registro no encontrado'}), 404
    return jsonify({'mensaje': 'Registro actualizado'})


# ── RESUMEN DE ASISTENCIA / DESCUENTOS (requiere admin) ──────────────────

@app.route('/api/resumen', methods=['POST'])
@jwt_required()
def post_resumen():
    """
    Body: { usuario_id, periodo: 'YYYY-MM', monto_por_falta }
    Calcula dias habiles del mes (lunes a viernes), dias asistidos,
    faltas, faltas ya justificadas, tardanzas, y lo guarda.

    La forma de "penalizar" las faltas depende de tipo_persona:
      - empleado:   descuento de dinero = faltas_con_descuento * monto_por_falta
                     (igual que antes).
      - estudiante: NO se descuenta dinero. Se calcula el % de inasistencia
                     (faltas no justificadas / dias habiles) y si supera
                     config.UMBRAL_INASISTENCIA_ESTUDIANTE, pierde_curso = True.
                     monto_por_falta se ignora para estudiantes aunque el
                     frontend lo mande.
    Las tardanzas NO restan nota ni generan descuento en ningun caso,
    solo quedan contabilizadas para que el admin las vea.
    """
    data = request.get_json()
    usuario_id      = data['usuario_id']
    periodo         = data['periodo']            # 'YYYY-MM'
    monto_por_falta = float(data.get('monto_por_falta', 0))

    usuario = obtener_usuario_por_id(usuario_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    anio, mes = map(int, periodo.split('-'))
    _, ultimo_dia = calendar.monthrange(anio, mes)
    desde = date(anio, mes, 1)
    hasta = date(anio, mes, ultimo_dia)

    dias_habiles = sum(
        1 for d in range(1, ultimo_dia + 1)
        if date(anio, mes, d).weekday() < 5   # 0-4 = lunes a viernes
    )

    historial = obtener_historial(usuario_id=usuario_id, limite=1000)
    ingresos_del_mes = {
        str(h['fecha']) for h in historial
        if h['tipo_evento'] == 'ingreso' and desde <= h['fecha'] <= hasta
    }
    tardanzas = sum(
        1 for h in historial
        if h['tipo_evento'] == 'ingreso' and h['fuera_de_horario'] and desde <= h['fecha'] <= hasta
    )

    dias_asistidos = len(ingresos_del_mes)
    faltas = max(dias_habiles - dias_asistidos, 0)

    justificaciones = listar_justificaciones(usuario_id, desde, hasta)
    faltas_justificadas = sum(1 for j in justificaciones if j['tipo'] == 'falta')

    # Faltas que NO tienen justificacion: son las que realmente penalizan,
    # sea como descuento (empleado) o como % de inasistencia (estudiante).
    faltas_sin_justificar = max(faltas - faltas_justificadas, 0)

    es_empleado = usuario['tipo_persona'] == 'empleado'

    descuento_calculado      = 0.0
    porcentaje_inasistencia  = 0.0
    pierde_curso             = False

    if es_empleado:
        descuento_calculado = round(faltas_sin_justificar * monto_por_falta, 2)
    else:
        porcentaje_inasistencia = round((faltas_sin_justificar / dias_habiles) * 100, 1) if dias_habiles else 0.0
        pierde_curso = (porcentaje_inasistencia / 100) > config.UMBRAL_INASISTENCIA_ESTUDIANTE

    guardar_resumen_periodo(
        usuario_id, periodo, dias_habiles, dias_asistidos, faltas,
        faltas_justificadas, tardanzas, monto_por_falta, descuento_calculado,
        pierde_curso, porcentaje_inasistencia
    )

    return jsonify({
        'tipo_persona': usuario['tipo_persona'],
        'periodo': periodo, 'dias_habiles': dias_habiles, 'dias_asistidos': dias_asistidos,
        'faltas': faltas, 'faltas_justificadas': faltas_justificadas,
        'faltas_con_descuento': faltas_sin_justificar, 'tardanzas': tardanzas,
        # Solo aplica a empleados (queda en 0 para estudiantes):
        'descuento_calculado': descuento_calculado,
        # Solo aplica a estudiantes (queda en 0/False para empleados):
        'porcentaje_inasistencia': porcentaje_inasistencia,
        'umbral_inasistencia_pct': round(config.UMBRAL_INASISTENCIA_ESTUDIANTE * 100, 1),
        'pierde_curso': pierde_curso
    })


# ── LOGIN DE ADMINISTRADOR ────────────────────────────────────────────────

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    token, nombre = login_password(data.get('usuario', ''), data.get('password', ''))
    if not token:
        return jsonify({'error': 'Usuario o contrasena incorrectos'}), 401
    return jsonify({'token': token, 'nombre': nombre})


@app.route('/api/admin/login-facial', methods=['POST'])
def admin_login_facial():
    data = request.get_json()
    vector = vector_desde_base64(data.get('imagen_base64', ''))
    if vector is None:
        return jsonify({'error': 'No se detecto un rostro valido'}), 400
    token, nombre = login_facial(vector)
    if not token:
        return jsonify({'error': 'Rostro no reconocido como administrador'}), 401
    return jsonify({'token': token, 'nombre': nombre})


@app.route('/api/admin/registrar-rostro', methods=['POST'])
@jwt_required()
def admin_registrar_rostro():
    """Un admin ya logueado (por password) agrega su rostro para poder loguearse asi despues."""
    admin_id = int(get_jwt_identity())
    data = request.get_json()
    vector = vector_desde_base64(data.get('imagen_base64', ''))
    if vector is None:
        return jsonify({'error': 'No se detecto un rostro valido'}), 400
    ok = guardar_vector_facial_admin(admin_id, vector_a_json(vector))
    return jsonify({'mensaje': 'Rostro guardado' if ok else 'Error al guardar'}), (200 if ok else 500)


# ── AUDIO ────────────────────────────────────────────────────────────────

# NOTA: la ruta /api/audio/<filename> que servia audio desde disco local
# ya no existe. Los audios ahora se suben a Supabase Storage (bucket
# 'audios') y audio_url en cada respuesta ya es la URL publica completa,
# lista para usar directo en el <audio src="...">.


# ── INICIO ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Servidor iniciado en http://localhost:5000')
    app.run(debug=True, port=int(os.getenv('FLASK_PORT', 5000)))
