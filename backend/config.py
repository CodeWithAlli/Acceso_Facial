# backend/config.py
# Configuracion global del sistema (migrado a Supabase / Postgres)

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # --- Conexion a Supabase (Postgres) ---
    # En Supabase Dashboard > Project Settings > Database > Connection string
    # (usa el modo "Session" o "Transaction pooler" segun tu plan).
    # Formato: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    # --- Supabase Storage (buckets 'rostros' y 'audios') ---
    # Sacalos de Supabase Dashboard > Project Settings > API.
    # SUPABASE_URL es la "Project URL". SUPABASE_SERVICE_KEY es la
    # "service_role" key (NO la "anon" key) -- solo esta puede subir
    # archivos sin depender de politicas RLS del bucket. Nunca la
    # expongas al frontend.
    SUPABASE_URL         = os.getenv('SUPABASE_URL', '')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')

    # --- Seguridad ---
    SECRET_KEY           = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY        = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 8))

    # --- Archivos (legado: ya no se usa, las fotos van a Supabase Storage) ---
    UPLOAD_FOLDER      = os.getenv('UPLOAD_FOLDER', 'backend/uploads/fotos')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    # --- Reconocimiento facial (SFace + coseno) ---
    # 0.363 es el umbral de referencia que recomienda OpenCV Zoo para SFace.
    SIMILARITY_THRESHOLD       = float(os.getenv('SIMILARITY_THRESHOLD', 0.363))
    # Umbral separado (mas exigente) para el login facial del administrador.
    SIMILARITY_THRESHOLD_ADMIN = float(os.getenv('SIMILARITY_THRESHOLD_ADMIN', 0.45))

    # --- Umbral de inasistencia para estudiantes (pierden el curso, no se
    # les descuenta dinero como a un empleado). 0.30 = 30% de los dias
    # habiles del periodo, la regla tipica del sistema educativo peruano.
    # Ajustable si tu reglamento usa otro porcentaje.
    UMBRAL_INASISTENCIA_ESTUDIANTE = float(os.getenv('UMBRAL_INASISTENCIA_ESTUDIANTE', 0.30))

    # --- Horario laboral por defecto (si el usuario no tiene uno propio) ---
    HORA_ENTRADA_DEFAULT = os.getenv('HORA_ENTRADA_DEFAULT', '08:00')
    HORA_SALIDA_DEFAULT  = os.getenv('HORA_SALIDA_DEFAULT', '17:00')
    TOLERANCIA_MINUTOS   = int(os.getenv('TOLERANCIA_MINUTOS', 10))


config = Config()
