# backend/db.py
# Conexion a Supabase (Postgres) y funciones para todas las tablas.
#
# Migrado desde MySQL: se usa psycopg2 en vez de mysql-connector, y las
# consultas usan sintaxis Postgres (RETURNING en vez de lastrowid, TRUE/
# FALSE en vez de 1/0, etc). La forma de llamar a estas funciones desde
# app.py no cambio casi nada.

import psycopg2
import psycopg2.extras
from backend.config import config


def get_connection():
    """Retorna una conexion activa a Supabase (Postgres)."""
    try:
        conn = psycopg2.connect(config.DATABASE_URL)
        return conn
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None


# ================================================================
# ADMINISTRADORES
# ================================================================

def obtener_admin_por_usuario(usuario: str):
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT * FROM administradores WHERE usuario = %s AND activo = TRUE', (usuario,))
        return cur.fetchone()
    finally:
        conn.close()


def obtener_admins_con_vector_facial() -> list:
    """Para el login facial del admin: trae solo los que tienen rostro registrado."""
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT id, nombre, vector_facial FROM administradores WHERE vector_facial IS NOT NULL AND activo = TRUE')
        return cur.fetchall()
    finally:
        conn.close()


def guardar_vector_facial_admin(admin_id: int, vector_facial_json: str) -> bool:
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(
            'UPDATE administradores SET vector_facial = %s::jsonb WHERE id = %s',
            (vector_facial_json, admin_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ================================================================
# USUARIOS (empleados / estudiantes)
# ================================================================

def crear_usuario(nombre_completo: str, dni: str, tipo_persona: str):
    """Crea un usuario y retorna su ID. None si el DNI ya existe."""
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO usuarios (nombre_completo, dni, tipo_persona) VALUES (%s, %s, %s) RETURNING id',
            (nombre_completo, dni, tipo_persona)
        )
        uid = cur.fetchone()[0]
        conn.commit()
        return uid
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None
    finally:
        conn.close()


def obtener_usuario_por_id(uid: int):
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT * FROM usuarios WHERE id = %s', (uid,))
        return cur.fetchone()
    finally:
        conn.close()


def buscar_usuarios(termino: str) -> list:
    """
    Busqueda para el dashboard del administrador: por nombre completo O
    por DNI (para que la busqueda del admin sea rapida, como pediste).
    """
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT * FROM usuarios
            WHERE nombre_completo ILIKE %s OR dni ILIKE %s
            ORDER BY nombre_completo
        ''', (f'%{termino}%', f'%{termino}%'))
        return cur.fetchall()
    finally:
        conn.close()


def listar_usuarios() -> list:
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT * FROM usuarios ORDER BY creado_en DESC')
        return cur.fetchall()
    finally:
        conn.close()


# ================================================================
# ROSTROS
# ================================================================

def guardar_rostro(usuario_id: int, imagen_path: str, vector_facial_json: str) -> bool:
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO rostros (usuario_id, imagen_path, vector_facial) VALUES (%s, %s, %s::jsonb)',
            (usuario_id, imagen_path, vector_facial_json)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def obtener_rostros_todos() -> list:
    """Todos los embeddings ya calculados, listos para comparar (sin releer imagenes)."""
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT r.usuario_id, r.vector_facial, u.nombre_completo AS nombre, u.dni
            FROM rostros r
            JOIN usuarios u ON r.usuario_id = u.id
            WHERE u.activo = TRUE
        ''')
        return cur.fetchall()
    finally:
        conn.close()


# ================================================================
# ACCESOS (ingreso / salida, 1 de cada uno por dia)
# ================================================================

def accesos_de_hoy(usuario_id: int) -> dict:
    """Retorna {'ingreso': row|None, 'salida': row|None} para hoy."""
    conn = get_connection()
    if not conn: return {'ingreso': None, 'salida': None}
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT * FROM accesos
            WHERE usuario_id = %s AND fecha = CURRENT_DATE
        ''', (usuario_id,))
        filas = cur.fetchall()
        resultado = {'ingreso': None, 'salida': None}
        for f in filas:
            resultado[f['tipo_evento']] = f
        return resultado
    finally:
        conn.close()


def registrar_acceso(usuario_id: int, tipo_evento: str, fuera_de_horario: bool = False):
    """
    tipo_evento: 'ingreso' o 'salida'.
    La restriccion UNIQUE (usuario_id, tipo_evento, fecha) de la tabla
    impide que se inserte un segundo registro del mismo tipo el mismo dia.
    """
    conn = get_connection()
    if not conn: return None
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO accesos (usuario_id, tipo_evento, fuera_de_horario)
            VALUES (%s, %s, %s)
            RETURNING id, hora
        ''', (usuario_id, tipo_evento, fuera_de_horario))
        fila = cur.fetchone()
        conn.commit()
        return {'id': fila[0], 'hora': fila[1]}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None
    finally:
        conn.close()


def editar_acceso_manual(acceso_id: int, nueva_hora, admin_id: int) -> bool:
    """El administrador corrige manualmente un ingreso/salida (requiere login)."""
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE accesos
            SET hora = %s, editado_manualmente = TRUE, editado_por = %s
            WHERE id = %s
        ''', (nueva_hora, admin_id, acceso_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def obtener_historial(usuario_id: int = None, limite: int = 50) -> list:
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if usuario_id:
            cur.execute('''
                SELECT a.*, u.nombre_completo, u.dni
                FROM accesos a JOIN usuarios u ON a.usuario_id = u.id
                WHERE a.usuario_id = %s
                ORDER BY a.hora DESC LIMIT %s
            ''', (usuario_id, limite))
        else:
            cur.execute('''
                SELECT a.*, u.nombre_completo, u.dni
                FROM accesos a JOIN usuarios u ON a.usuario_id = u.id
                ORDER BY a.hora DESC LIMIT %s
            ''', (limite,))
        return cur.fetchall()
    finally:
        conn.close()


# ================================================================
# JUSTIFICACIONES
# ================================================================

def crear_justificacion(usuario_id: int, fecha, tipo: str, motivo: str, admin_id: int) -> bool:
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO justificaciones (usuario_id, fecha, tipo, motivo, aprobado_por)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (usuario_id, fecha) DO UPDATE
                SET tipo = EXCLUDED.tipo, motivo = EXCLUDED.motivo, aprobado_por = EXCLUDED.aprobado_por
        ''', (usuario_id, fecha, tipo, motivo, admin_id))
        conn.commit()
        return True
    finally:
        conn.close()


def listar_justificaciones(usuario_id: int, desde, hasta) -> list:
    conn = get_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('''
            SELECT * FROM justificaciones
            WHERE usuario_id = %s AND fecha BETWEEN %s AND %s
        ''', (usuario_id, desde, hasta))
        return cur.fetchall()
    finally:
        conn.close()


# ================================================================
# RESUMEN / DESCUENTOS
# ================================================================

def guardar_resumen_periodo(usuario_id, periodo, dias_habiles, dias_asistidos,
                             faltas, faltas_justificadas, tardanzas,
                             monto_por_falta, descuento_calculado,
                             pierde_curso=False, porcentaje_inasistencia=0.0) -> bool:
    conn = get_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO resumen_periodo
                (usuario_id, periodo, dias_habiles, dias_asistidos, faltas,
                 faltas_justificadas, tardanzas, monto_por_falta, descuento_calculado,
                 pierde_curso, porcentaje_inasistencia)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (usuario_id, periodo) DO UPDATE SET
                dias_habiles = EXCLUDED.dias_habiles,
                dias_asistidos = EXCLUDED.dias_asistidos,
                faltas = EXCLUDED.faltas,
                faltas_justificadas = EXCLUDED.faltas_justificadas,
                tardanzas = EXCLUDED.tardanzas,
                monto_por_falta = EXCLUDED.monto_por_falta,
                descuento_calculado = EXCLUDED.descuento_calculado,
                pierde_curso = EXCLUDED.pierde_curso,
                porcentaje_inasistencia = EXCLUDED.porcentaje_inasistencia
        ''', (usuario_id, periodo, dias_habiles, dias_asistidos, faltas,
              faltas_justificadas, tardanzas, monto_por_falta, descuento_calculado,
              pierde_curso, porcentaje_inasistencia))
        conn.commit()
        return True
    finally:
        conn.close()
