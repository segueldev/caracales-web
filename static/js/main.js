/* =============================================================================
   ACADEMIA FELINA FLOPPA - LIQUID GLASS INTERACTIONS
   =============================================================================
   Adaptado del prototipo "Club Felino Floppa" - mantiene:
   - Música de fondo con control de volumen persistente
   - Efecto de burbujas en hover (navbar)
   - Sonidos de click (vidrio) en navegación
   - Animaciones de entrada de página
   ============================================================================= */

$(document).ready(function() {
  // =========================================================================
  // 1. CONTROLADOR DE MÚSICA DE FONDO Y VOLUMEN
  // =========================================================================
  const audio = document.getElementById('bgMusic');
  const btnMusic = document.getElementById('btnMusic');
  const musicIcon = document.getElementById('musicIcon');
  const musicVolume = document.getElementById('musicVolume');
  const mewAudio = document.getElementById('mewSound');

  if (mewAudio) {
    mewAudio.load(); // Forzar pre-carga
  }

  if (audio && btnMusic && musicIcon && musicVolume) {
    // Cargar volumen guardado o por defecto a 0.40 (40%)
    let savedVolume = localStorage.getItem('musicVolume');
    let currentVolume = savedVolume !== null ? parseFloat(savedVolume) : 0.40;
    
    audio.volume = currentVolume;
    musicVolume.value = currentVolume;

    // Comprobar si estaba reproduciéndose anteriormente
    const storedPlaying = localStorage.getItem('musicPlaying');
    const shouldPlay = (storedPlaying === 'true') && currentVolume > 0;

    if (shouldPlay) {
      audio.play().then(() => {
        musicIcon.textContent = '🔊';
      }).catch(err => {
        console.log("Autoplay bloqueado al navegar:", err);
        audio.pause();
        musicIcon.textContent = '🔇';
        localStorage.setItem('musicPlaying', 'false');
      });
    } else {
      audio.pause();
      musicIcon.textContent = '🔇';
    }

    // Alternar reproducción con el botón altavoz
    btnMusic.addEventListener('click', function(e) {
      e.preventDefault();
      if (audio.paused) {
        if (audio.volume === 0) {
          audio.volume = 0.40;
          musicVolume.value = 0.40;
          localStorage.setItem('musicVolume', 0.40);
        }
        audio.play().then(() => {
          musicIcon.textContent = '🔊';
          localStorage.setItem('musicPlaying', 'true');
        }).catch(err => {
          console.error("Error al reproducir audio:", err);
        });
      } else {
        audio.pause();
        musicIcon.textContent = '🔇';
        localStorage.setItem('musicPlaying', 'false');
      }
    });

    // Controlador del slider de volumen en tiempo real
    musicVolume.addEventListener('input', function() {
      const newVol = parseFloat(this.value);
      audio.volume = newVol;
      localStorage.setItem('musicVolume', newVol);

      if (newVol === 0) {
        audio.pause();
        musicIcon.textContent = '🔇';
        localStorage.setItem('musicPlaying', 'false');
      } else {
        if (audio.paused && localStorage.getItem('musicPlaying') === 'true') {
          audio.play().then(() => {
            musicIcon.textContent = '🔊';
          }).catch(err => console.log(err));
        } else if (!audio.paused) {
          musicIcon.textContent = '🔊';
        }
      }
    });
  }

  // =========================================================================
  // 2. EFECTO DE BURBUJAS EN HOVER (Navbar links) Y CLICS
  // =========================================================================
  const hoverSounds = [
    document.getElementById('hoverSound1'),
    document.getElementById('hoverSound2')
  ].filter(s => s);
  
  const clickSound = document.getElementById('clickSound');

  $('.navbar-nav-floppa a').on('mouseenter', function() {
    const $link = $(this);
    const $parent = $link.parent(); // Elemento <li> para evitar recortar desbordes

    // Reproducir sonido hover aleatorio
    if (hoverSounds.length > 0) {
      const sound = hoverSounds[Math.floor(Math.random() * hoverSounds.length)];
      sound.volume = 0.12;
      sound.currentTime = 0;
      sound.play().catch(e => console.log('Audio bloqueado en hover:', e));
    }

    // Generar dinámicamente entre 4 y 6 burbujas
    const numBubbles = Math.floor(Math.random() * 3) + 4; // 4, 5 o 6
    for (let i = 0; i < numBubbles; i++) {
      const $bubble = $('<span class="burbuja"></span>');
      const size = Math.random() * 6 + 6; // Entre 6px y 12px
      const x = Math.random() * $link.outerWidth();
      const delay = Math.random() * 0.3; // Retraso escalonado

      $bubble.css({
        width: size + 'px',
        height: size + 'px',
        left: x + 'px',
        bottom: '0px',
        animationDelay: delay + 's'
      });

      $parent.append($bubble);

      // Eliminar burbuja al finalizar su animación
      setTimeout(function() {
        $bubble.remove();
      }, 1100); // 800ms animación + retraso + margen
    }
  });

  $('.navbar-nav-floppa a').on('click', function(e) {
    const href = $(this).attr('href');
    const target = $(this).attr('target');
    
    if (href && href !== '#' && !href.startsWith('javascript:')) {
      e.preventDefault();
      
      // Reproducir clickvidrio.mp3
      if (clickSound) {
        clickSound.volume = 0.25;
        clickSound.currentTime = 0;
        clickSound.play().catch(e => console.log('Audio bloqueado en clic:', e));
      }

      // Pequeño retardo para oír el sonido antes de navegar
      setTimeout(function() {
        if (target === '_blank') {
          window.open(href, '_blank', 'noopener,noreferrer');
        } else {
          window.location.href = href;
        }
      }, 150);
    }
  });

  // Botón banner image (si existe)
  $('.btn-imagen-link').on('click', function(e) {
    const href = $(this).attr('href');
    if (href) {
      e.preventDefault();
      
      if (mewAudio) {
        mewAudio.currentTime = 0;
        mewAudio.volume = 0.35;
        mewAudio.play().catch(e => console.log('Audio bloqueado en clic banner:', e));
      }

      // Retardo de 400ms para oír el maullido completo antes de navegar
      setTimeout(function() {
        window.location.href = href;
      }, 400);
    }
  });
});

// =========================================================================
// 3. SONIDO DE ÉXITO (Web Audio API) - Vidrio / Agua
// =========================================================================
let audioCtx = null;

function getCtx() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return null;
  if (!audioCtx) audioCtx = new AudioContextClass();
  return audioCtx;
}

function glassTing(ctx, start, freq, gain) {
  const osc = ctx.createOscillator();
  const env = ctx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(freq, start);
  env.gain.setValueAtTime(0, start);
  env.gain.linearRampToValueAtTime(gain, start + 0.008);
  env.gain.exponentialRampToValueAtTime(0.0001, start + 0.9);
  osc.connect(env).connect(ctx.destination);
  osc.start(start);
  osc.stop(start + 1.0);
}

function waterDrop(ctx, start) {
  const osc = ctx.createOscillator();
  const env = ctx.createGain();
  osc.type = 'sine';
  osc.frequency.setValueAtTime(900, start);
  osc.frequency.exponentialRampToValueAtTime(360, start + 0.14);
  env.gain.setValueAtTime(0, start);
  env.gain.linearRampToValueAtTime(0.22, start + 0.01);
  env.gain.exponentialRampToValueAtTime(0.0001, start + 0.28);
  osc.connect(env).connect(ctx.destination);
  osc.start(start);
  osc.stop(start + 0.3);
}

function playSuccessSound() {
  const ctx = getCtx();
  if (!ctx) return;
  
  if (ctx.state === 'suspended') {
    ctx.resume();
  }

  const t = ctx.currentTime;
  
  // Glass chime: E6, A6, E7 major-ish shimmer
  glassTing(ctx, t, 1318.51, 0.16); // E6
  glassTing(ctx, t + 0.04, 1760.0, 0.12); // A6
  glassTing(ctx, t + 0.09, 2637.02, 0.07); // E7
  
  // Water drop underneath
  waterDrop(ctx, t + 0.02);
}

// Exponer globalmente para uso en templates
window.playSuccessSound = playSuccessSound;

// =========================================================================
// 4. UTILIDADES GLOBALES
// =========================================================================

/**
 * Descompone un ISO 8601 del API en sus partes, SIN convertir de huso horario.
 *
 * Devuelve { anio, mes, dia, hora, minuto } o null si el valor no es una fecha.
 * Se apoya en una expresión regular en vez de new Date() porque:
 *   - new Date('11/01/2026') asume MM/DD/AAAA y puede devolver otra fecha;
 *   - new Date('23/10/2026') devuelve Invalid Date (no existe el mes 23);
 *   - new Date() convierte a la hora local del navegador, que puede mover
 *     el día hacia atrás.
 *
 * Ejemplos:
 *   '2026-11-01T04:52:24+00:00' -> {anio:'2026', mes:'11', dia:'01', hora:'04', minuto:'52'}
 *   '2026-11-01'                -> {anio:'2026', mes:'11', dia:'01', hora:null,  minuto:null}
 */
function descomponerFecha(valor) {
  if (!valor) return null;
  const m = String(valor).match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/);
  if (!m) return null;
  return { anio: m[1], mes: m[2], dia: m[3], hora: m[4] || null, minuto: m[5] || null };
}

window.AcademiaFloppa = {
  // Obtener token de acceso
  getToken: () => localStorage.getItem('access_token'),
  
  // Verificar si está autenticado
  isAuthenticated: () => !!localStorage.getItem('access_token'),
  
  // Headers estándar para API
  apiHeaders: () => ({
    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
  }),
  
  // Formatear precio CLP
  formatCLP: (value) => {
    return 'CLP ' + parseFloat(value || 0).toLocaleString('es-CL');
  },

  /**
   * Precio en pesos chilenos con el billete al lado (formato pedido):
   *   precioHTML(499990) -> 'CLP 499.990 <img class="ico-peso" ...>'
   *   precioHTML(79990)  -> 'CLP 79.990  <img class="ico-peso" ...>'
   * El separador de miles lo pone toLocaleString('es-CL') (punto chileno).
   * Devuelve HTML, así que hay que usarlo con .html() y no con .text().
   */
  precioHTML: (value) => {
    const monto = parseFloat(value || 0).toLocaleString('es-CL');
    const icono = window.ICONO_PESO;
    if (!icono) return 'CLP ' + monto;
    return `CLP ${monto} <img class="ico-peso" src="${icono}" alt="CLP" title="Pesos chilenos">`;
  },
  
  // ---------------------------------------------------------------------
  // FECHA LEGIBLE - ver el bloque en academia_felina/settings.py (DATETIME_FORMAT)
  //
  // El API entrega ISO 8601: "2026-11-01T04:52:24+00:00".
  // NO se usa new Date().toLocaleDateString() por dos motivos:
  //
  //   1. Desempaca SÓLO la parte de fecha y la reordena a dd-mm-aaaa.
  //      Si el día viera antes del mes (11 de noviembre) se produce una
  //      fecha distinta a la que envió el servidor, según el navegador.
  //   2. NO convierte de zona horaria. Un curso que empieza el 1 de noviembre
  //      tiene que decir "01-11-2026" también para quien entre desde otra
  //      zona horaria; si el reloj UTC cae entre 00:00 y 03:00, toLocaleDateString()
  //      lo retrocedería un día completo.
  //
  // fechaHTML('2026-11-01T04:52:24+00:00') -> '01-11-2026'
  // fechaHTML('2026-11-01')               -> '01-11-2026'
  // fechaHoraHTML(...)                    -> '01-11-2026 04:52'
  // ---------------------------------------------------------------------
  fechaHTML: (valor) => {
    const p = descomponerFecha(valor);
    if (!p) return valor ? String(valor) : '-';
    return `${p.dia}-${p.mes}-${p.anio}`;
  },

  fechaHoraHTML: (valor) => {
    const p = descomponerFecha(valor);
    if (!p) return valor ? String(valor) : '-';
    const hora = p.hora ? ` ${p.hora}:${p.minuto}` : '';
    return `${p.dia}-${p.mes}-${p.anio}${hora}`;
  },
  
  // Mostrar toast/notificación
  toast: (message, type = 'success') => {
    const alertClass = type === 'success' ? 'alert-success' : 
                       type === 'error' ? 'alert-danger' : 
                       type === 'warning' ? 'alert-warning' : 'alert-info';
    
    const toast = $(`
      <div class="alert ${alertClass} alert-dismissible fade show glass-dark position-fixed" 
           style="top: 80px; right: 20px; z-index: 9999; min-width: 300px; max-width: 400px;"
           role="alert">
        ${message}
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
      </div>
    `);
    
    $('body').append(toast);
    setTimeout(() => toast.alert('close'), 5000);
  }
};

// Atajo global: los templates llaman a precioHTML(...) directamente.
window.precioHTML = AcademiaFloppa.precioHTML;
// Atajos de fecha: los templates (catálogo, carro, matrículas, panel del
// coordinador) pintan fechas con fechaHTML(...) para que todas salgan igual.
window.fechaHTML = AcademiaFloppa.fechaHTML;
window.fechaHoraHTML = AcademiaFloppa.fechaHoraHTML;

// CSRF token para AJAX
$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", $('[name=csrfmiddlewaretoken]').val());
    }
  }
});
// =========================================================================
// 6. CIERRE DE SESIÓN (navbar)
// =========================================================================
// El botón #btnLogout envía un <form method="post"> a /logout/ (Django sólo
// acepta POST ahí). Aquí se intercepta ese submit para hacer DOS cosas antes
// de que la página se recargue:
//
//   1. Revocar el refresh token en la blacklist del backend
//      -> POST /api/auth/logout/ con el Bearer + el refresh guardado.
//   2. Borrar access_token y refresh_token de localStorage
//      -> sin eso, los recursos JavaScript seguirían llamando a la API como
//         si el usuario siguiera dentro, y el "cerrar sesión" sería un
//         adorno visual sin efecto real.
//
// `HTMLFormElement.prototype.submit.call(form)` dispara el envío del
// formulario SIN volver a pasar por este manejador (no re-lanza el evento
// submit), así que no hay bucle infinito.
$(document).on('submit', '#formLogout', function (event) {
  event.preventDefault();

  const form = this;
  const access = localStorage.getItem('access_token');
  const refresh = localStorage.getItem('refresh_token');

  // Se borran primero: aunque la petición de revocación falle por cualquier
  // motivo, el navegador ya no conserva credenciales del usuario.
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  const enviarFormulario = function () {
    HTMLFormElement.prototype.submit.call(form);
  };

  if (!refresh) {
    enviarFormulario();
    return;
  }

  fetch('/api/auth/logout/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + (access || '')
    },
    body: JSON.stringify({ refresh: refresh })
  })
    .catch(function () {})          // si falla, se ignora: lo importante es salir
    .finally(enviarFormulario);    // y en cualquier caso se cierra la sesión
});
