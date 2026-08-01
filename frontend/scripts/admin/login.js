// frontend/scripts/admin/login.js

function guardarSesion(token, nombre) {
  localStorage.setItem('admin_token', token);
  localStorage.setItem('admin_nombre', nombre);
  window.location.href = 'dashboard.html';
}

async function loginPassword() {
  const usuario  = document.getElementById('admin-usuario').value.trim();
  const password = document.getElementById('admin-password').value;
  try {
    const res  = await fetch(`${API}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usuario, password })
    });
    const data = await res.json();
    if (res.ok) {
      guardarSesion(data.token, data.nombre);
    } else {
      mostrarResultado(`❌ ${data.error}`, false);
    }
  } catch (e) {
    mostrarResultado('Error de conexion con el servidor', false);
  }
}

async function loginFacial() {
  if (!hayRostro()) { mostrarResultado('No hay rostro detectado', false); return; }

  // --- LIVENESS CHECK (mismo criterio que marcarAsistencia en auth.js) ---
  // Sin esto, el login facial del admin aceptaba una foto o pantalla
  // estatica igual que cualquier usuario normal, pese a dar acceso a
  // editar registros y calcular descuentos.
  if (typeof seDetectoParpadeo === 'function' && !seDetectoParpadeo()) {
    mostrarResultado('⚠️ Por seguridad, parpadea frente a la cámara antes de continuar', false);
    return;
  }

  const imagen_base64 = capturaFrame();
  try {
    const res  = await fetch(`${API}/admin/login-facial`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ imagen_base64 })
    });
    const data = await res.json();
    if (res.ok) {
      guardarSesion(data.token, data.nombre);
    } else {
      mostrarResultado(`❌ ${data.error}`, false);
    }
  } catch (e) {
    mostrarResultado('Error de conexion con el servidor', false);
  } finally {
    if (typeof reiniciarParpadeo === 'function') reiniciarParpadeo();
  }
}
