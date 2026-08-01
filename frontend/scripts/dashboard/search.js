// frontend/scripts/dashboard/search.js
// El dashboard evalua a UNA persona a la vez (no a todos juntos), buscada
// por nombre o por DNI (para que el admin la encuentre rapido).

let personaActual = null;

async function buscarPersona() {
  const termino = document.getElementById('buscar-input').value.trim();
  if (!termino) return;

  const token = localStorage.getItem('admin_token');
  const { ok, data } = await fetchJSON(`${API}/personas?buscar=${encodeURIComponent(termino)}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const divResultados = document.getElementById('resultados-busqueda');

  if (!ok && data && data.msg) {
    // Token vencido o invalido -> el backend respondio 401/422
    localStorage.removeItem('admin_token');
    window.location.href = 'login.html';
    return;
  }

  if (!ok || data.length === 0) {
    divResultados.innerHTML = '<p style="color:#ff7b72">No se encontraron personas</p>';
    document.getElementById('panel-persona').classList.add('oculto');
    return;
  }

  if (data.length === 1) {
    seleccionarPersona(data[0]);
    divResultados.innerHTML = '';
    return;
  }

  divResultados.innerHTML = data.map(p => `
    <button onclick='seleccionarPersonaPorId(${p.id})' style="display:block;width:100%;margin-top:6px">
      ${p.nombre_completo} — DNI ${p.dni}
    </button>
  `).join('');
  window._personasEncontradas = data;
}

function seleccionarPersonaPorId(id) {
  const p = window._personasEncontradas.find(x => x.id === id);
  if (p) seleccionarPersona(p);
}

function seleccionarPersona(persona) {
  personaActual = persona;
  document.getElementById('panel-persona').classList.remove('oculto');
  document.getElementById('persona-nombre').textContent = persona.nombre_completo;
  document.getElementById('persona-dni').textContent = persona.dni;
  document.getElementById('persona-tipo').textContent = persona.tipo_persona;

  // El descuento en dinero solo aplica a empleados; a un estudiante se
  // le evalua % de inasistencia (ver calcularResumen en admin.js), asi
  // que ese campo no tiene sentido para el y se oculta.
  const esEmpleado = persona.tipo_persona === 'empleado';
  document.getElementById('monto-falta-campo').classList.toggle('oculto', !esEmpleado);

  // Limpiar el resumen de la persona anterior para no mostrar datos viejos
  document.getElementById('resumen-panel').classList.add('oculto');

  cargarHistorial(persona.id);
  cargarGrafico(persona.id);
}
