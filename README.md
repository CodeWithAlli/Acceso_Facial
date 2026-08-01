# Sistema de Acceso Facial - Asistencia (Supabase)

Sistema de control de asistencia por reconocimiento facial para empresa o
colegio. Marca ingreso y salida automaticamente (una vez cada uno por dia),
calcula faltas y descuentos, y permite justificar inasistencias desde un
panel de administrador.

## Requisitos previos
- Python 3.10+
- Cuenta de Supabase (gratis) con un proyecto creado
- Node no es necesario para correr el proyecto (el frontend es HTML/JS plano)

## 1. Base de datos (Supabase)
1. Entra a tu proyecto en https://supabase.com/dashboard
2. Ve a **SQL Editor > New query**
3. Copia y pega el contenido de `database/supabase_schema.sql` y dale **Run**
4. Copia y pega el contenido de `database/supabase_seed.sql` y dale **Run**
5. Copia y pega el contenido de `database/migracion_estudiantes.sql` y dale **Run**
   (esto crea un admin de prueba: usuario `admin`, clave `admin123` — cambiala luego)
6. Ve a **Project Settings > Database > Connection string > URI** y copia esa URL

## 2. Backend
```bash
cd backend
python -m venv venv
venv/Scripts/activate          # en Windows
pip install -r requirements.txt --break-system-packages
```

Edita el archivo `.env` en la raiz del proyecto y pega tu connection string
de Supabase en `DATABASE_URL`.

### Descargar los modelos de reconocimiento facial
Estos 2 archivos no vienen incluidos por su peso. Instrucciones exactas en
`backend/models/DESCARGAR_MODELOS.txt`.

### Levantar el servidor
```bash
cd ..
python -m backend.app
```
Debe quedar escuchando en `http://localhost:5000`

## 3. Frontend
Levanta el frontend con el servidor simple de Python
```bash
cd frontend
python -m http.server 5500
```
Abre en el navegador:
http://localhost:5500

## Flujo de uso
1. **Registrar persona**: en la pagina principal, escribe nombre completo,
   DNI y tipo (empleado/estudiante), y presiona "Capturar y Registrar".
2. **Marcar asistencia**: la persona simplemente se para frente a la camara
   — el sistema detecta el rostro, espera a que este estable, y marca
   automaticamente ingreso (primera vez del dia) o salida (segunda vez).
   Un tercer intento el mismo dia no se registra de nuevo.
3. **Panel de administrador** (`login.html`): con password o con rostro.
   Desde el dashboard se puede buscar a una persona (por nombre o DNI),
   ver su historial, calcular el resumen de faltas/descuento del mes, y
   justificar una falta o tardanza.

## Estructura del proyecto
```
backend/
  app.py              endpoints REST (Flask)
  auth.py             login de administrador (password o rostro)
  db.py               acceso a Supabase (Postgres)
  config.py           variables de configuracion
  utils/vector_tools.py   reconocimiento facial (YuNet + SFace)
  utils/voice.py      audios de bienvenida/despedida (gTTS)
  models/             modelos .onnx (se descargan aparte)
database/
  supabase_schema.sql tablas
  supabase_seed.sql   admin de prueba
frontend/
  index.html          camara + registro + marcado automatico
  login.html           login del administrador
  dashboard.html       busqueda de persona, historial, resumen, justificaciones
docs/
  documentacion del proyecto (ver Word entregado aparte)
```

## Notas importantes
- El backend habla con Supabase directo (Postgres), el frontend nunca toca
  Supabase directamente, siempre pasa por la API Flask.
- El umbral de similitud facial (`SIMILARITY_THRESHOLD` en `.env`) se debe
  ajustar con pruebas reales en tu ambiente (iluminacion, camara).
