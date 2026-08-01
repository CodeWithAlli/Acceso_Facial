# backend/utils/storage_supabase.py
# Sube archivos a los buckets de Supabase Storage (rostros, audios) y
# devuelve su URL publica. Reemplaza el guardado en disco local:
#
# - En Render (y la mayoria de hosts gratuitos) el disco es EFIMERO:
#   se borra cada vez que el servicio se reinicia o se redespliega.
#   Guardar en Supabase Storage hace que las fotos y audios sobrevivan
#   a los reinicios.
# - De paso, la URL publica que devuelve Supabase ya es una URL
#   absoluta (https://...supabase.co/...), asi que el frontend no
#   necesita saber en que dominio vive el backend para reproducir el
#   audio: voice.js ya sabe usar la URL tal cual si empieza con 'http'.
#
# IMPORTANTE: usa la SERVICE ROLE KEY (no la anon key) porque es la
# unica que puede subir archivos sin depender de politicas RLS del
# bucket. Esa key SOLO debe vivir en el backend (.env), nunca en el
# frontend ni en el repositorio.

from supabase import create_client
from backend.config import config

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
            raise RuntimeError(
                'Faltan SUPABASE_URL y/o SUPABASE_SERVICE_KEY en el .env. '
                'Sacalos de Supabase Dashboard > Project Settings > API.'
            )
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    return _client


def subir_archivo(bucket: str, nombre_archivo: str, datos: bytes, content_type: str) -> str:
    """
    Sube `datos` (bytes) al bucket indicado y devuelve la URL publica final.
    Los buckets 'rostros' y 'audios' deben existir y estar en modo Public
    (ya los creaste en el Dashboard, asi que solo hace falta esto).
    """
    client = _get_client()
    client.storage.from_(bucket).upload(
        path=nombre_archivo,
        file=datos,
        file_options={'content-type': content_type, 'upsert': 'true'}
    )
    return client.storage.from_(bucket).get_public_url(nombre_archivo)
