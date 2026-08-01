// frontend/scripts/dashboard/history.js
async function cargarHistorial(usuario_id) {
  const token = localStorage.getItem('admin_token');
  const { ok, data } = await fetchJSON(`${API}/historial?usuario_id=${usuario_id}&limite=100`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!ok) return;

  const tbody = document.getElementById('tabla-historial');
  tbody.innerHTML = data.map(row => `
    <tr>
      <td><span class='badge-${row.tipo_evento}'>${row.tipo_evento.toUpperCase()}</span></td>
      <td>${row.fecha}</td>
      <td>${new Date(row.hora).toLocaleTimeString()}</td>
      <td>${row.fuera_de_horario ? '⚠️ Sí' : 'No'}</td>
      <td><button class='secundario' style='width:auto;padding:6px 12px;font-size:0.78rem' onclick='editarRegistro(${row.id})'>Editar</button></td>
    </tr>
  `).join('');
}
