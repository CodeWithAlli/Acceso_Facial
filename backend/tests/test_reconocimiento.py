# backend/tests/test_reconocimiento.py
# Script manual de verificacion rapida (no es un test de pytest estricto,
# solo confirma que el pipeline de deteccion + embedding funciona con una
# foto real). Reemplaza "cara.jpg" por una foto con un rostro visible.

from backend.utils.vector_tools import extraer_vector

ruta = "backend/uploads/fotos/cara.jpg"

vector = extraer_vector(ruta)

print("VECTOR:")
print(vector)

if vector is not None:
    print("Se detecto un rostro. Dimension del embedding:", vector.shape)
else:
    print("No se detecto rostro en la imagen. Prueba con otra foto.")
