// frontend/scripts/core/auth.js
// Registra el evento de asistencia (ingreso o salida, decidido por el
// backend automáticamente) mediante acción manual por botón.

async function marcarAsistencia() {
  if (!hayRostro()) { 
    mostrarResultado('❌ No hay rostro detectado frente a la cámara', false); 
    return; 
  }

  // --- LIVENESS CHECK (Validación local de parpadeo) ---
  if (typeof seDetectoParpadeo === 'function' && !seDetectoParpadeo()) {
    mostrarResultado('⚠️ Por seguridad, parpadea frente a la cámara antes de marcar', false);
    return;
  }

  const imagen_base64 = capturaFrame();
  const btnAutenticar = document.getElementById('btn-autenticar');
  
  // Bloqueamos el botón temporalmente para evitar doble envío continuo
  if (btnAutenticar) {
    btnAutenticar.disabled = true;
    btnAutenticar.textContent = '⏳ Procesando rostro...';
  }

  // Asegura la ruta correcta apuntando a /api/evento
  const baseUrl = (typeof API !== 'undefined') ? API : 'http://localhost:5000';
  const urlEndpoint = baseUrl.endsWith('/api') ? `${baseUrl}/evento` : `${baseUrl}/api/evento`;

  try {
    const res = await fetch(urlEndpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ imagen_base64 })
    });
    const data = await res.json();

    if (!data.acceso) {
      mostrarResultado(`🚫 ${data.mensaje || 'Acceso denegado'}`, false);
      if (data.audio_url && typeof window.reproducirAudio === 'function') {
        window.reproducirAudio(data.audio_url);
      }
      return;
    }

    if (data.evento === 'ingreso') {
      mostrarResultado(`✅ Bienvenido, ${data.nombre}${data.fuera_de_horario ? ' (tardanza)' : ''}`, true);
    } else if (data.evento === 'salida') {
      mostrarResultado(`👋 Hasta pronto, ${data.nombre}${data.fuera_de_horario ? ' (salida anticipada)' : ''}`, true);
    } else {
      mostrarResultado(`ℹ️ ${data.mensaje}`, true);
    }

    // Reproducción del audio dinámico de bienvenida/despedida
    if (data.audio_url && typeof window.reproducirAudio === 'function') {
      window.reproducirAudio(data.audio_url);
    }
  } catch (e) {
    console.error('Error al enviar evento de asistencia:', e);
    mostrarResultado('Error de conexion con el servidor', false);
  } finally {
    // Reseteamos el parpadeo local para exigir un nuevo parpadeo en el siguiente marcaje
    if (typeof reiniciarParpadeo === 'function') {
      reiniciarParpadeo();
    }

    // Restablecemos el botón después de terminar la petición
    if (btnAutenticar) {
      btnAutenticar.disabled = false;
      btnAutenticar.textContent = '📸 Marcar asistencia ahora';
    }
  }
}

// Desactivamos la ejecución automática en bucle
function onRostroEstable() {
  console.log("Rostro estable detectado, esperando pulsación de botón...");
}

// Botón manual: intercepta el evento (e) para evitar que el navegador recargue la página
function iniciarAutenticacion(e) { 
  if (e && typeof e.preventDefault === 'function') {
    e.preventDefault(); // 🛑 FRENO DE MANO: Cancela la recarga por el formulario
  }
  marcarAsistencia(); 
}

// NOTA: el binding al clic ya lo hace el atributo onclick="iniciarAutenticacion(event)"
// en index.html. No se agrega un addEventListener adicional aqui porque
// duplicaba la llamada a marcarAsistencia() en cada clic (dos peticiones
// a /api/evento y el audio reproduciendose superpuesto dos veces).

// Exportación explícita a la ventana global para vinculación con los eventos HTML
window.marcarAsistencia = marcarAsistencia;
window.iniciarAutenticacion = iniciarAutenticacion;
window.onRostroEstable = onRostroEstable;