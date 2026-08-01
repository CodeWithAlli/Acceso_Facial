// frontend/scripts/core/face.js
// Inicializa MediaPipe FaceMesh (solo para overlay visual y para saber
// "cuando capturar" en el navegador) y expone capturaFrame().
//
// El reconocimiento de identidad NO se hace aqui ni con estos landmarks:
// eso lo hace el backend con SFace. Esto solo dibuja la malla y decide
// el momento de disparar la captura automatica.

const video  = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx    = canvas.getContext('2d');
const estado = document.getElementById('estado');

let ultimosLandmarks = null;

// --- Detección de Parpadeo (Liveness Check) ---
const UMBRAL_EAR = 0.21; // EAR menor a esto se considera ojo cerrado
let ojoEstabaCerrado = false;
let parpadeoConfirmado = false;

// Distancia euclidiana entre 2 puntos 2D/3D
function calcularDistancia(p1, p2) {
  return Math.hypot(p1.x - p2.x, p1.y - p2.y);
}

// Eye Aspect Ratio (EAR)
function calcularEAR(landmarks, indicesOjo) {
  // Puntos verticales del ojo
  const v1 = calcularDistancia(landmarks[indicesOjo[1]], landmarks[indicesOjo[5]]);
  const v2 = calcularDistancia(landmarks[indicesOjo[2]], landmarks[indicesOjo[4]]);
  // Punto horizontal
  const h  = calcularDistancia(landmarks[indicesOjo[0]], landmarks[indicesOjo[3]]);
  
  return (v1 + v2) / (2.0 * h);
}

// Landmarks canónicos de MediaPipe Face Mesh para los ojos
const OJO_IZQUIERDO = [33, 160, 158, 133, 153, 144];
const OJO_DERECHO   = [362, 385, 387, 263, 373, 380];

function procesarParpadeo(landmarks) {
  const earIzq = calcularEAR(landmarks, OJO_IZQUIERDO);
  const earDer = calcularEAR(landmarks, OJO_DERECHO);
  const earPromedio = (earIzq + earDer) / 2;

  // Si los ojos se cierran
  if (earPromedio < UMBRAL_EAR) {
    ojoEstabaCerrado = true;
  } 
  // Cuando vuelven a abrirse tras haber sido cerrados
  else if (ojoEstabaCerrado) {
    ojoEstabaCerrado = false;
    parpadeoConfirmado = true; // Parpadeo completado
  }
}

function reiniciarParpadeo() {
  ojoEstabaCerrado = false;
  parpadeoConfirmado = false;
}

// --- Auto-captura: dispara sola cuando el rostro esta estable ---
const FRAMES_ESTABLE_REQUERIDOS = 20;  // ~0.6-1s segun fps de camara
const COOLDOWN_MS = 6000;              // no repetir captura antes de 6s
let framesConRostro = 0;
let ultimaCapturaAutomatica = 0;
let modoAutomaticoActivo = false;       // se desactiva mientras se esta registrando

function habilitarModoAutomatico(activo) {
  modoAutomaticoActivo = activo;
  framesConRostro = 0;
  if (activo) reiniciarParpadeo();
}

const faceMesh = new FaceMesh({
  locateFile: f => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}`
});

faceMesh.setOptions({
  maxNumFaces: 1,
  refineLandmarks: true,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5
});

faceMesh.onResults(results => {
  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const hayRostroAhora = results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0;

  if (hayRostroAhora) {
    ultimosLandmarks = results.multiFaceLandmarks[0];
    drawConnectors(ctx, ultimosLandmarks, FACEMESH_TESSELATION,
      { color: '#30363d', lineWidth: 0.5 });
    drawLandmarks(ctx, ultimosLandmarks,
      { color: '#58a6ff', lineWidth: 0.5, radius: 1 });

    // Evaluar si la persona parpadeó
    procesarParpadeo(ultimosLandmarks);

    // Feedback visual en el mensaje de estado
    if (!parpadeoConfirmado) {
      estado.textContent = 'Parpadea para verificar...';
      estado.style.color = '#e3b341'; // Amarillo/Naranja
    } else {
      estado.textContent = 'Rostro real detectado';
      estado.style.color = '#56d364'; // Verde
    }

    framesConRostro++;
    const yaPasoCooldown = (Date.now() - ultimaCapturaAutomatica) > COOLDOWN_MS;
    
    // CONDICIÓN MEJORADA: Requiere rostro estable + PARPADEO REAL
    if (modoAutomaticoActivo && framesConRostro >= FRAMES_ESTABLE_REQUERIDOS && yaPasoCooldown && parpadeoConfirmado) {
      ultimaCapturaAutomatica = Date.now();
      framesConRostro = 0;
      reiniciarParpadeo(); // Reseteamos para exigirlo nuevamente en el siguiente ciclo
      
      if (typeof onRostroEstable === 'function') onRostroEstable();
    }
  } else {
    ultimosLandmarks = null;
    framesConRostro = 0;
    reiniciarParpadeo();
    estado.textContent = 'Sin rostro...';
    estado.style.color = '#ff7b72';
  }
});

const camera = new Camera(video, {
  onFrame: async () => { await faceMesh.send({ image: video }); },
  width: 640, height: 480
});
camera.start();

/** Captura el frame actual como base64 JPEG */
function capturaFrame() {
  const tmp = document.createElement('canvas');
  tmp.width  = video.videoWidth;
  tmp.height = video.videoHeight;
  tmp.getContext('2d').drawImage(video, 0, 0);
  return tmp.toDataURL('image/jpeg', 0.9);
}

/** Retorna true si hay un rostro detectado en este momento */
function hayRostro() { return ultimosLandmarks !== null; }

/** Retorna true si el usuario ya parpadeó al menos una vez */
function seDetectoParpadeo() { return parpadeoConfirmado; }