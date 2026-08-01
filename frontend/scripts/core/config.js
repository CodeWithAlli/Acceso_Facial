// frontend/scripts/core/config.js
// ÚNICA fuente de verdad para la URL del backend. Antes cada archivo
// (register.js, search.js, login.js) declaraba su propio "const API"
// apuntando a localhost -> si dos de esos scripts se cargaban juntos en
// la misma pagina, el navegador lanzaba "Identifier 'API' has already
// been declared" y rompía TODO el JS de esa página en silencio.
//
// Este archivo debe cargarse PRIMERO, antes que cualquier otro <script>
// de frontend/scripts/, en index.html, dashboard.html y login.html.

// 👉 CUANDO DESPLIEGUES EL BACKEND (Render, Railway, Fly.io, etc.),
//    reemplaza esta URL por la de tu backend en producción.
//    Supabase por si solo NO puede alojar este servidor Flask: Supabase
//    aquí actúa solo como base de datos (Postgres). El backend Flask
//    necesita un host de aplicaciones (Render/Railway funcionan bien
//    y tienen plan gratuito).
const BACKEND_URL_PRODUCCION = 'https://TU-BACKEND-EN-RENDER.onrender.com';

const ES_LOCAL = ['localhost', '127.0.0.1', ''].includes(window.location.hostname);

// URL "raiz" del backend, SIN sufijo /api (para armar audio_url, imágenes, etc.)
const API_BASE_URL = ES_LOCAL ? 'http://localhost:5000' : BACKEND_URL_PRODUCCION;

// URL para llamadas REST, CON sufijo /api (usada por todos los fetch existentes)
const API = `${API_BASE_URL}/api`;

// Se exponen explícitamente en window para que cualquier script que se
// cargue después (aunque no comparta el mismo scope de módulo) las use.
window.API_BASE_URL = API_BASE_URL;
window.API = API;
