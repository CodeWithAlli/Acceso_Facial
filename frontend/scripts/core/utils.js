// frontend/scripts/core/utils.js
// Funciones comunes compartidas por todos los módulos

/**
 * Muestra una notificación tipo Toast en la pantalla
 * @param {string} mensaje - Texto a mostrar
 * @param {string} tipo - 'exito', 'error', 'advertencia' o 'info'
 * @param {number} duracion - Tiempo en ms (default: 4000)
 */
function mostrarToast(mensaje, tipo = 'info', duracion = 4000) {
  let container = document.getElementById('toast-container');
  
  // Si no existe el contenedor flotante en la página, lo crea
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${tipo}`;
  toast.innerHTML = `<span>${mensaje}</span>`;

  container.appendChild(toast);

  // Ocultar y remover el toast automáticamente
  setTimeout(() => {
    toast.style.animation = 'fadeOut 0.3s ease-in forwards';
    toast.addEventListener('animationend', () => {
      toast.remove();
    });
  }, duracion);
}

/**
 * Muestra el resultado de una acción. 
 * Mantiene compatibilidad actualizando el div #resultado y lanzando un Toast.
 */
function mostrarResultado(mensaje, exito) {
  // 1. Compatibilidad con tu div #resultado
  const div = document.getElementById('resultado');
  if (div) {
    div.textContent = mensaje;
    div.className   = 'resultado ' + (exito ? 'exito' : 'error');
    setTimeout(() => { div.className = 'resultado oculto'; }, 4000);
  }

  // 2. Notificación flotante Toast
  const tipoToast = exito ? 'exito' : 'error';
  mostrarToast(mensaje, tipoToast);
}

// La funcion reproducirAudio() vivia duplicada aqui Y en voice.js, cada
// una con una URL distinta (una hardcodeada a localhost, sin soporte para
// produccion). Ahora existe una sola version, en voice.js, cargada donde
// se necesita reproducir audio (index.html).

async function fetchJSON(url, opciones = {}) {
  const res  = await fetch(url, opciones);
  const data = await res.json();
  return { ok: res.ok, data };
}