-- database/supabase_seed.sql
-- Ejecutar DESPUES de supabase_schema.sql.
-- Crea un administrador inicial con password (cambialo apenas entres).
--
-- La contrasena de este seed es "admin123" ya hasheada con bcrypt.
-- Genera tu propio hash con: python -c "import bcrypt; print(bcrypt.hashpw(b'tu_clave', bcrypt.gensalt()).decode())"

INSERT INTO administradores (nombre, usuario, password_hash)
VALUES (
    'Administrador Principal',
    'admin',
    '$2b$12$4wT3w4Cd6/sDBeoch0b8ROkwv7nLM4In99zdSuCPpxPyfW7S.9P.O'  -- corresponde a "admin123"
);
