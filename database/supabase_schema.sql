-- database/supabase_schema.sql
-- Esquema completo para Supabase (PostgreSQL).
-- Ejecutar en: Supabase Dashboard > SQL Editor > New query > pegar todo > Run.
--
-- Reemplaza por completo a database/schema.sql (que era para MySQL/XAMPP).
-- Orden de creacion importa por las llaves foraneas.

-- ============================================================
-- 1. ADMINISTRADORES (login del panel: password o rostro)
-- ============================================================
CREATE TABLE administradores (
    id             BIGSERIAL PRIMARY KEY,
    nombre         TEXT NOT NULL,
    usuario        TEXT UNIQUE NOT NULL,
    password_hash  TEXT,              -- bcrypt; null si solo usara login facial
    vector_facial  JSONB,             -- embedding SFace 128-d; null si solo usara password
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT admin_necesita_credencial CHECK (password_hash IS NOT NULL OR vector_facial IS NOT NULL)
);

-- ============================================================
-- 2. USUARIOS (empleados o estudiantes que marcan asistencia)
-- ============================================================
CREATE TABLE usuarios (
    id                     BIGSERIAL PRIMARY KEY,
    nombre_completo        TEXT NOT NULL,
    dni                    VARCHAR(20) UNIQUE NOT NULL,
    tipo_persona           TEXT NOT NULL CHECK (tipo_persona IN ('empleado', 'estudiante')),
    activo                 BOOLEAN NOT NULL DEFAULT TRUE,
    hora_entrada_esperada  TIME,          -- ej 08:00:00 -> para detectar tardanzas
    hora_salida_esperada   TIME,          -- ej 17:00:00 -> para detectar salida anticipada
    creado_en              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usuarios_dni    ON usuarios (dni);
CREATE INDEX idx_usuarios_nombre ON usuarios (nombre_completo);

-- ============================================================
-- 3. ROSTROS (embedding facial, calculado UNA vez al registrar)
-- ============================================================
CREATE TABLE rostros (
    id             BIGSERIAL PRIMARY KEY,
    usuario_id     BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    imagen_path    TEXT NOT NULL,
    vector_facial  JSONB NOT NULL,        -- embedding SFace, 128 numeros
    creado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_rostros_usuario ON rostros (usuario_id);

-- ============================================================
-- 4. ACCESOS (ingreso / salida, maximo 1 de cada uno por dia)
-- ============================================================
CREATE TABLE accesos (
    id                    BIGSERIAL PRIMARY KEY,
    usuario_id            BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo_evento           TEXT NOT NULL CHECK (tipo_evento IN ('ingreso', 'salida')),
    fecha                 DATE NOT NULL DEFAULT CURRENT_DATE,
    hora                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    fuera_de_horario      BOOLEAN NOT NULL DEFAULT FALSE,
    editado_manualmente   BOOLEAN NOT NULL DEFAULT FALSE,
    editado_por           BIGINT REFERENCES administradores(id),
    -- Esta restriccion es la que garantiza a nivel de base de datos que
    -- no pueda existir mas de 1 ingreso y mas de 1 salida por persona por dia.
    UNIQUE (usuario_id, tipo_evento, fecha)
);

CREATE INDEX idx_accesos_usuario_fecha ON accesos (usuario_id, fecha);

-- ============================================================
-- 5. JUSTIFICACIONES (faltas/tardanzas justificadas por el admin)
-- ============================================================
CREATE TABLE justificaciones (
    id            BIGSERIAL PRIMARY KEY,
    usuario_id    BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    fecha         DATE NOT NULL,
    tipo          TEXT NOT NULL CHECK (tipo IN ('falta', 'tardanza', 'salida_temprana')),
    motivo        TEXT NOT NULL,
    aprobado_por  BIGINT NOT NULL REFERENCES administradores(id),
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Solo puede haber una justificacion por persona por dia.
    UNIQUE (usuario_id, fecha)
);

-- ============================================================
-- 6. RESUMEN DE ASISTENCIA / DESCUENTOS (reemplaza la tabla
--    "rendimiento" academica original, que no aplicaba al caso real)
-- ============================================================
CREATE TABLE resumen_periodo (
    id                    BIGSERIAL PRIMARY KEY,
    usuario_id            BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    periodo               TEXT NOT NULL,      -- formato 'YYYY-MM', ej '2026-07'
    dias_habiles          INTEGER NOT NULL DEFAULT 0,
    dias_asistidos        INTEGER NOT NULL DEFAULT 0,
    faltas                INTEGER NOT NULL DEFAULT 0,
    faltas_justificadas   INTEGER NOT NULL DEFAULT 0,
    tardanzas             INTEGER NOT NULL DEFAULT 0,
    monto_por_falta       NUMERIC(10,2) NOT NULL DEFAULT 0,   -- lo define el admin (solo aplica a empleados)
    descuento_calculado   NUMERIC(10,2) NOT NULL DEFAULT 0,   -- solo aplica a empleados
    pierde_curso          BOOLEAN NOT NULL DEFAULT FALSE,     -- solo aplica a estudiantes
    porcentaje_inasistencia NUMERIC(5,2) NOT NULL DEFAULT 0,  -- solo aplica a estudiantes
    generado_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (usuario_id, periodo)
);

-- ============================================================
-- Seguridad: Row Level Security
-- ============================================================
-- El backend Flask se conecta con la connection string de Postgres
-- (rol postgres / service role), NO con la anon key. Por eso el
-- frontend JAMAS habla directo con Supabase: siempre pasa por la API
-- Flask. Aun asi, se deja RLS activado por buena practica -- si en el
-- futuro se agrega acceso directo desde el frontend con supabase-js,
-- estas tablas quedan bloqueadas hasta definir politicas explicitas.
ALTER TABLE administradores  ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios         ENABLE ROW LEVEL SECURITY;
ALTER TABLE rostros          ENABLE ROW LEVEL SECURITY;
ALTER TABLE accesos          ENABLE ROW LEVEL SECURITY;
ALTER TABLE justificaciones  ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumen_periodo  ENABLE ROW LEVEL SECURITY;
-- (sin politicas = nadie entra por la API publica de Supabase; el
-- backend Flask usa la conexion directa a Postgres, que no pasa por RLS
-- via PostgREST del mismo modo -- ver docs/migracion_supabase.docx)
