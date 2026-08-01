// frontend/scripts/core/voice.js
// Manejo de reproducción de audio sincronizado con el backend y Web Speech API

const synth = window.speechSynthesis;

/**
 * Reproduce los audios MP3 retornados por el backend en /api/audio/...
 * @param {string} url - Ruta relativa enviada por el servidor (ej: /api/audio/bienvenida_1.mp3)
 */
function reproducirAudio(url) {
  if (!url) return;

  // Busca el elemento <audio id="audio-respuesta"> del index.html o crea uno
  let audio = document.getElementById('audio-respuesta');
  if (!audio) {
    audio = document.createElement('audio');
    audio.id = 'audio-respuesta';
    document.body.appendChild(audio);
  }

  // Define la URL RAIZ del servidor Flask (SIN /api): audio_url ya viene
  // como '/api/audio/archivo.mp3', asi que si aqui usaramos la variable
  // API (que SI incluye '/api') terminariamos con '.../api/api/audio/...'
  // -> 404. Este era el motivo de que el audio se generara en el backend
  // pero nunca se escuchara en el navegador.
  const baseUrl = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://localhost:5000';

  // Si la url ya viene completa la usa, si es relativa le antepone la base
  const rutaFinal = url.startsWith('http') ? url : `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`;

  audio.src = rutaFinal;

  // Carga y reproduce el archivo de audio
  audio.load();
  audio.play()
    .then(() => {
      console.log("🔊 Audio reproducido desde:", rutaFinal);
    })
    .catch(e => {
      console.warn('⚠️ El navegador bloqueó o no encontró el audio:', e);
    });
}

/**
 * Síntesis de voz local en el navegador (Web Speech API)
 */
function hablarNavegador(texto, lang = 'es-ES') {
  if (!synth) return;
  synth.cancel();
  const utter = new SpeechSynthesisUtterance(texto);
  utter.lang  = lang;
  utter.rate  = 1.0;
  utter.pitch = 1.0;
  synth.speak(utter);
}

// Exportar explícitamente al objeto window para que auth.js y el HTML puedan llamarlas
window.reproducirAudio = reproducirAudio;
window.hablarNavegador = hablarNavegador;