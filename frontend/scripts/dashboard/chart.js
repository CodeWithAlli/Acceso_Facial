// frontend/scripts/dashboard/chart.js
let graficoActual = null;
let graficoFaltasActual = null;

// Colores tomados de las variables CSS de main.css (tema "papel claro"),
// antes este grafico usaba una paleta de tema oscuro (#e6edf3/#8b949e/#21262d)
// que no combinaba con el fondo claro real de la app y se veia deslavado.
const COLOR_INK      = '#2A2E33';
const COLOR_INK_SOFT = '#6B7280';
const COLOR_BORDER   = '#E3E0D8';
const COLOR_ACCENT   = '#386772'; // teal institucional, informativo (tardanzas)
const COLOR_SAGE     = '#4C7A5E'; // verde, exito/justificado
const COLOR_BRICK    = '#A6473F'; // terracota, alerta (descuento / pierde curso)
const COLOR_AMBER    = '#B8863B'; // mostaza, neutral (faltas totales)

async function cargarGrafico(usuario_id) {
  const token = localStorage.getItem('admin_token');
  const { ok, data } = await fetchJSON(`${API}/historial?usuario_id=${usuario_id}&limite=200`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!ok) return;

  const conteo = Array(24).fill(0);
  data.forEach(row => {
    const hora = new Date(row.hora).getHours();
    conteo[hora]++;
  });

  if (graficoActual) graficoActual.destroy();

  const ctx = document.getElementById('grafico-horas').getContext('2d');
  graficoActual = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: Array.from({length:24}, (_,i) => `${i}:00`),
      datasets: [{ label: 'Accesos', data: conteo, backgroundColor: COLOR_ACCENT, borderRadius: 4 }]
    },
    options: {
      plugins: { legend: { labels: { color: COLOR_INK } } },
      scales: {
        x: { ticks: { color: COLOR_INK_SOFT }, grid: { color: COLOR_BORDER } },
        y: { ticks: { color: COLOR_INK_SOFT }, grid: { color: COLOR_BORDER } }
      }
    }
  });
}

/**
 * Grafico de barras con el resumen de faltas del periodo calculado en
 * calcularResumen() (admin.js). Se adapta segun tipo_persona:
 *  - empleado: la 3ra barra es el descuento en dinero.
 *  - estudiante: la 3ra barra es el % de inasistencia.
 * Esa 3ra barra se pinta de rojo (COLOR_BRICK) solo cuando el resultado
 * es realmente negativo (hay descuento > 0, o pierde el curso); si no,
 * usa un color neutro para no alarmar sin motivo.
 * @param {object} resumen - la respuesta de POST /api/resumen
 */
function cargarGraficoFaltas(resumen) {
  if (graficoFaltasActual) graficoFaltasActual.destroy();

  const esEmpleado = resumen.tipo_persona === 'empleado';

  const tercerLabel = esEmpleado ? 'Con descuento (S/.)' : '% Inasistencia';
  const tercerValor  = esEmpleado ? resumen.descuento_calculado : resumen.porcentaje_inasistencia;
  const hayAlerta    = esEmpleado ? resumen.descuento_calculado > 0 : resumen.pierde_curso;
  const colorTercero = hayAlerta ? COLOR_BRICK : COLOR_ACCENT;

  const ctx = document.getElementById('grafico-faltas').getContext('2d');
  graficoFaltasActual = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Faltas totales', 'Justificadas', tercerLabel, 'Tardanzas'],
      datasets: [{
        data: [resumen.faltas, resumen.faltas_justificadas, tercerValor, resumen.tardanzas],
        backgroundColor: [COLOR_AMBER, COLOR_SAGE, colorTercero, COLOR_ACCENT],
        borderRadius: 4
      }]
    },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: COLOR_INK_SOFT, precision: 0 }, grid: { color: COLOR_BORDER } },
        y: { ticks: { color: COLOR_INK }, grid: { display: false } }
      }
    }
  });
}
