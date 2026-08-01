# backend/tests/test_db.py
from backend.db import get_connection, listar_usuarios

def test_conexion_bd():
    conn = get_connection()
    assert conn is not None
    assert conn.closed == 0   # psycopg2: 0 = conexion abierta
    conn.close()

def test_listar_usuarios_retorna_lista():
    resultado = listar_usuarios()
    assert isinstance(resultado, list)
