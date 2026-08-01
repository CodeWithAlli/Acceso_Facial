# backend/utils/voice.py
# Genera audio con gTTS para las respuestas de voz del kiosco y lo sube
# directo al bucket 'audios' de Supabase Storage (sin tocar el disco
# local). Retorna la URL PUBLICA final, lista para usar en <audio src>.
#
# Antes esto se guardaba en disco local (backend/uploads/audio/) y
# app.py exponia una ruta /api/audio/<archivo> para servirlo. Eso se
# quito por dos motivos:
# 1. En Render (y la mayoria de hosts gratuitos) el disco es EFIMERO:
#    se borra en cada redeploy o reinicio.
#    de correr, cambiaba segun donde se lanzara el proceso.
# 2. Con Supabase Storage, la URL publica ya es absoluta
#    (https://...supabase.co/...), asi que ni siquiera hace falta que
#    el frontend sepa el dominio del backend para reproducirla.
#
# Los nombres de archivo usan el ID del usuario (no el nombre) para evitar
# problemas con espacios/tildes y para no pisar el audio de una persona
# con el de otra que tenga un nombre parecido.

from io import BytesIO
from gtts import gTTS

from backend.utils.storage_supabase import subir_archivo

BUCKET_AUDIOS = 'audios'


def generar_audio(texto: str, nombre_archivo: str) -> str:
    """Genera el MP3 en memoria, lo sube al bucket 'audios' y retorna su URL publica."""
    tts = gTTS(text=texto, lang='es', slow=False)
    buffer = BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return subir_archivo(BUCKET_AUDIOS, f'{nombre_archivo}.mp3', buffer.read(), 'audio/mpeg')


def audio_bienvenida(usuario_id: int, nombre: str) -> str:
    primer_nombre = nombre.strip().split(' ')[0]
    return generar_audio(f'Bienvenido, {primer_nombre}', f'bienvenida_{usuario_id}')


def audio_despedida(usuario_id: int, nombre: str) -> str:
    primer_nombre = nombre.strip().split(' ')[0]
    return generar_audio(f'Hasta pronto, {primer_nombre}', f'despedida_{usuario_id}')


def audio_ya_registrado(nombre: str) -> str:
    primer_nombre = nombre.strip().split(' ')[0]
    return generar_audio(
        f'{primer_nombre}, ya registraste tu ingreso y tu salida de hoy',
        'ya_registrado_generico'
    )


def audio_acceso_denegado() -> str:
    return generar_audio('Acceso denegado. Rostro no reconocido.', 'denegado')
