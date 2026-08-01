-- database/migracion_estudiantes.sql
--
-- Ejecuta esto UNA VEZ en Supabase > SQL Editor si tu base de datos ya
-- existia antes de este cambio (o sea, ya corriste supabase_schema.sql
-- antes de hoy). Si vas a crear la base de datos desde cero, no hace
-- falta: ya viene incluido en supabase_schema.sql.
--
-- Agrega las 2 columnas que necesita la logica separada para
-- estudiantes (pierden el curso por % de inasistencia, no se les
-- descuenta dinero como a un empleado).

ALTER TABLE resumen_periodo
    ADD COLUMN IF NOT EXISTS pierde_curso BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS porcentaje_inasistencia NUMERIC(5,2) NOT NULL DEFAULT 0;
