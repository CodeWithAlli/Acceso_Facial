// frontend/scripts/dashboard/admin.js
// Acciones que requieren sesion de administrador (token guardado en
// localStorage por login.html). Si no hay sesion, se avisa y se manda
// a login.html en vez de dejar que el fetch falle en silencio.

(function exigirSesionAdmin() {
  const token  = localStorage.getItem('admin_token');
  const nombre = localStorage.getItem('admin_nombre');
  if (!token) {
    window.location.href = 'login.html';
    return;
  }
  document.getElementById('admin-estado').textContent = `Sesión activa: ${nombre}`;
})();

function cerrarSesionAdmin() {
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_nombre');
  window.location.href = 'login.html';
}

function tokenAdminOrRedirigir() {
  const token = localStorage.getItem('admin_token');
  if (!token) {
    alert('Necesitas iniciar sesion como administrador para esta accion');
    window.location.href = 'login.html';
    return null;
  }
  return token;
}

async function calcularResumen() {
  if (!personaActual) return;
  const token = tokenAdminOrRedirigir();
  if (!token) return;

  const periodo = document.getElementById('resumen-periodo').value;   // 'YYYY-MM'
  const monto_por_falta = parseFloat(document.getElementById('monto-por-falta').value) || 0;
  if (!periodo) { mostrarResultado('Selecciona un periodo (mes)', false); return; }

  const res = await fetch(`${API}/resumen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ usuario_id: personaActual.id, periodo, monto_por_falta })
  });
  const data = await res.json();

  const panel  = document.getElementById('resumen-panel');
  const badge  = document.getElementById('resumen-badge');
  const cards  = document.getElementById('resumen-cards');

  if (!res.ok) {
    panel.classList.add('oculto');
    mostrarResultado(data.msg || data.error || 'Error al calcular el resumen', false);
    return;
  }

  panel.classList.remove('oculto');

  // Tarjetas comunes a empleados y estudiantes
  let cardsHtml = `
    <div class='card'><div class='numero'>${data.dias_habiles}</div><div class='label'>Días hábiles</div></div>
    <div class='card'><div class='numero'>${data.dias_asistidos}</div><div class='label'>Asistidos</div></div>
    <div class='card'><div class='numero'>${data.faltas}</div><div class='label'>Faltas</div></div>
    <div class='card'><div class='numero'>${data.faltas_justificadas}</div><div class='label'>Justificadas</div></div>
    <div class='card'><div class='numero'>${data.tardanzas}</div><div class='label'>Tardanzas</div></div>
  `;

  if (data.tipo_persona === 'empleado') {
    // --- EMPLEADO: descuento monetario ---
    cardsHtml += `<div class='card'><div class='numero'>S/. ${data.descuento_calculado}</div><div class='label'>Descuento total</div></div>`;
    if (data.descuento_calculado > 0) {
      badge.className   = 'badge-estado mal';
      badge.textContent = `⚠️ Se aplica un descuento de S/. ${data.descuento_calculado} por ${data.faltas_con_descuento} falta(s) sin justificar`;
    } else {
      badge.className   = 'badge-estado ok';
      badge.textContent = '✅ Sin descuentos este periodo';
    }
  } else {
    // --- ESTUDIANTE: % de inasistencia contra el umbral (pierde el curso, no se le quita dinero) ---
    cardsHtml += `<div class='card'><div class='numero'>${data.porcentaje_inasistencia}%</div><div class='label'>Inasistencia (umbral ${data.umbral_inasistencia_pct}%)</div></div>`;
    if (data.pierde_curso) {
      badge.className   = 'badge-estado mal';
      badge.textContent = `🚫 Pierde el curso: ${data.porcentaje_inasistencia}% de inasistencia supera el umbral de ${data.umbral_inasistencia_pct}%`;
    } else if (data.porcentaje_inasistencia >= data.umbral_inasistencia_pct * 0.7) {
      badge.className   = 'badge-estado riesgo';
      badge.textContent = `⚠️ En riesgo: ${data.porcentaje_inasistencia}% de inasistencia (umbral ${data.umbral_inasistencia_pct}%)`;
    } else {
      badge.className   = 'badge-estado ok';
      badge.textContent = `✅ Asistencia dentro de lo permitido (${data.porcentaje_inasistencia}% de ${data.umbral_inasistencia_pct}%)`;
    }
  }

  cards.innerHTML = cardsHtml;
  if (typeof cargarGraficoFaltas === 'function') cargarGraficoFaltas(data);
}

async function guardarJustificacion() {
  if (!personaActual) return;
  const token = tokenAdminOrRedirigir();
  if (!token) return;

  const fecha  = document.getElementById('justificacion-fecha').value;
  const tipo   = document.getElementById('justificacion-tipo').value;
  const motivo = document.getElementById('justificacion-motivo').value.trim();
  if (!fecha || !motivo) { mostrarResultado('Completa fecha y motivo', false); return; }

  const res = await fetch(`${API}/justificaciones`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ usuario_id: personaActual.id, fecha, tipo, motivo })
  });
  const data = await res.json();
  const div = document.getElementById('justificacion-resultado');
  div.textContent = res.ok ? `✅ ${data.mensaje}` : `❌ ${data.error || data.msg}`;
}

async function editarRegistro(acceso_id) {
  const token = tokenAdminOrRedirigir();
  if (!token) return;

  const nuevaHora = prompt(
    'Nueva fecha y hora del registro (formato: AAAA-MM-DD HH:MM), ejemplo: 2026-07-07 08:15'
  );
  if (!nuevaHora) return;

  const res = await fetch(`${API}/accesos/${acceso_id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ hora: nuevaHora })
  });
  const data = await res.json();

  if (res.ok) {
    mostrarResultado('✅ Registro actualizado', true);
    cargarHistorial(personaActual.id);
    cargarGrafico(personaActual.id);
  } else {
    mostrarResultado(`❌ ${data.error || 'No se pudo editar el registro'}`, false);
  }
}
