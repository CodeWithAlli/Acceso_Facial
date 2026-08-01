# backend/auth.py
# Autenticacion del panel de administrador: con password (bcrypt) o con
# rostro (mismo pipeline SFace que usan los usuarios normales).
# Genera JWT con flask-jwt-extended para proteger los endpoints de edicion.

import bcrypt
from flask_jwt_extended import create_access_token
from datetime import timedelta

from backend.config import config
from backend.db import obtener_admin_por_usuario, obtener_admins_con_vector_facial
from backend.utils.vector_tools import similitud_coseno, vector_desde_json


def login_password(usuario: str, password: str):
    """Retorna (token, nombre_admin) o (None, None) si las credenciales son invalidas."""
    admin = obtener_admin_por_usuario(usuario)
    if not admin or not admin.get('password_hash'):
        return None, None
    if not bcrypt.checkpw(password.encode(), admin['password_hash'].encode()):
        return None, None
    token = create_access_token(
        identity=str(admin['id']),
        expires_delta=timedelta(hours=config.JWT_EXPIRATION_HOURS)
    )
    return token, admin['nombre']


def login_facial(vector_actual):
    """
    Compara el rostro contra los administradores que tienen rostro
    registrado. Usa un umbral MAS EXIGENTE que el de los usuarios
    normales (config.SIMILARITY_THRESHOLD_ADMIN) porque esto da acceso
    a editar registros y calcular descuentos.
    """
    admins = obtener_admins_con_vector_facial()
    mejor_sim = -1.0
    mejor_admin = None
    for admin in admins:
        vec_bd = vector_desde_json(admin['vector_facial'])
        sim = similitud_coseno(vector_actual, vec_bd)
        if sim > mejor_sim:
            mejor_sim = sim
            mejor_admin = admin

    if mejor_admin and mejor_sim >= config.SIMILARITY_THRESHOLD_ADMIN:
        token = create_access_token(
            identity=str(mejor_admin['id']),
            expires_delta=timedelta(hours=config.JWT_EXPIRATION_HOURS)
        )
        return token, mejor_admin['nombre']
    return None, None
