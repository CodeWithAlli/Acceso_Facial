// frontend/scripts/core/register.js
// Alta de una persona nueva (empleado o estudiante).
// Mientras se esta escribiendo el formulario, se desactiva la auto-captura
// (habilitarModoAutomatico) para que no dispare un /api/evento por error.

document.getElementById('nombre-input').addEventListener('focus', () => habilitarModoAutomatico(false));
document.getElementById('dni-input').addEventListener('focus', () => habilitarModoAutomatico(false));

async function iniciarRegistro() {
  const nombre_completo = document.getElementById('nombre-input').value.trim();
  const dni             = document.getElementById('dni-input').value.trim();
  const tipo_persona     = document.getElementById('tipo-persona-select').value;

  if (!nombre_completo) { mostrarResultado('Ingresa el nombre completo', false); return; }
  if (!dni)             { mostrarResultado('Ingresa el DNI', false); return; }
  if (!hayRostro())     { mostrarResultado('No hay rostro detectado', false); return; }

  // --- LIVENESS CHECK (mismo criterio que auth.js y login.js) ---
  if (typeof seDetectoParpadeo === 'function' && !seDetectoParpadeo()) {
    mostrarResultado('⚠️ Por seguridad, parpadea frente a la cámara antes de registrar', false);
    return;
  }

  const imagen_base64 = capturaFrame();

  try {
    const res  = await fetch(`${API}/registro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre_completo, dni, tipo_persona, imagen_base64 })
    });
    const data = await res.json();

    if (res.ok) {
      mostrarResultado(`✅ ${data.mensaje}`, true);
      document.getElementById('nombre-input').value = '';
      document.getElementById('dni-input').value = '';
    } else {
      mostrarResultado(`❌ ${data.error}`, false);
    }
  } catch (e) {
    mostrarResultado('Error de conexion con el servidor', false);
  } finally {
    habilitarModoAutomatico(true);
  }
}
