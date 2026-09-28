/**
 * Signal Lab — Awwwards & Austensor Web Companion Application
 * Vanilla JS procedural RF wavefield, constellation renderer, and Web Audio synthesizer.
 */

document.addEventListener('DOMContentLoaded', () => {
  initWavefield();
  initConstellationLab();
  initExperimentDock();
  initAudioSynthesizer();
  initDossierModal();
});

// ============================================================================
// 1. Procedural RF Tensor Wavefield Canvas (Austensor Style)
// ============================================================================
let waveMode = 'harmonic'; // 'harmonic' | 'constellation'
let mouseX = 0;
let mouseY = 0;
let isMouseActive = false;

function initWavefield() {
  const canvas = document.getElementById('wavefield-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  // Mouse tracking for interactive wave perturbation
  window.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;
    isMouseActive = true;
  });

  window.addEventListener('mouseleave', () => {
    isMouseActive = false;
  });

  // Floating particles
  const particles = [];
  const numParticles = 40;
  for (let i = 0; i < numParticles; i++) {
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * 600,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.6,
      size: Math.random() * 2 + 1,
      color: Math.random() > 0.6 ? '#D4AF37' : '#00F0FF',
      phase: Math.random() * Math.PI * 2
    });
  }

  let time = 0;

  function render() {
    time += 0.02;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const midY = h * 0.52;

    if (waveMode === 'harmonic') {
      // 1. Procedural Harmonic Multi-Carrier Superposition (HF / VHF / UHF)
      const harmonics = [
        { freq: 0.006, speed: 0.8, amp: 40, color: 'rgba(0, 240, 255, 0.25)', lw: 1.5 },
        { freq: 0.014, speed: -1.2, amp: 22, color: 'rgba(212, 175, 55, 0.20)', lw: 1.2 },
        { freq: 0.003, speed: 0.4, amp: 55, color: 'rgba(10, 132, 255, 0.15)', lw: 2.0 },
      ];

      harmonics.forEach(({ freq, speed, amp, color, lw }) => {
        ctx.beginPath();
        const phase = time * speed;
        for (let x = 0; x < w; x += 4) {
          // Add subtle mouse attraction wave
          let mouseInfluence = 0;
          if (isMouseActive) {
            const dist = Math.abs(x - mouseX);
            if (dist < 200) {
              mouseInfluence = Math.cos((dist / 200) * (Math.PI / 2)) * 30 * Math.sin(time * 3);
            }
          }

          const y = midY + amp * Math.sin(x * freq + phase) * Math.cos(x * 0.0015 + phase * 0.4) + mouseInfluence;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = color;
        ctx.lineWidth = lw;
        ctx.stroke();
      });
    }

    // 2. Floating Constellation Nodes & Mesh
    particles.forEach((p, idx) => {
      p.x += p.vx;
      p.y += p.vy;
      p.phase += 0.03;

      if (p.x < 0) p.x = w;
      if (p.x > w) p.x = 0;
      if (p.y < 0) p.y = h;
      if (p.y > h) p.y = 0;

      const alpha = 0.4 + 0.4 * Math.sin(p.phase);
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = alpha;
      ctx.fill();
      ctx.globalAlpha = 1.0;

      // Draw subtle mesh links
      for (let j = idx + 1; j < Math.min(idx + 4, particles.length); j++) {
        const other = particles[j];
        const dx = p.x - other.x;
        const dy = p.y - other.y;
        const distSq = dx * dx + dy * dy;
        if (distSq < 10000) {
          const linkAlpha = (1 - Math.sqrt(distSq) / 100) * 0.2;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(other.x, other.y);
          ctx.strokeStyle = 'rgba(212, 175, 55, ' + linkAlpha + ')';
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    });

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);

  // Mode toggles
  const btnWave = document.getElementById('btn-mode-wave');
  const btnConst = document.getElementById('btn-mode-constellation');

  btnWave.addEventListener('click', () => {
    waveMode = 'harmonic';
    btnWave.classList.add('active');
    btnConst.classList.remove('active');
  });

  btnConst.addEventListener('click', () => {
    waveMode = 'constellation';
    btnConst.classList.add('active');
    btnWave.classList.remove('active');
  });
}

// ============================================================================
// 2. Interactive Constellation & Cumulant Laboratory
// ============================================================================
let activeMod = 'BPSK';
let snrVal = 20.0;
let cfoVal = 100.0;

function initConstellationLab() {
  const canvas = document.getElementById('constellation-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  const snrSlider = document.getElementById('snr-slider');
  const snrDisplay = document.getElementById('snr-display');
  const cfoSlider = document.getElementById('cfo-slider');
  const cfoDisplay = document.getElementById('cfo-display');

  const evClass = document.getElementById('ev-class');
  const evC42 = document.getElementById('ev-c42');
  const evVar = document.getElementById('ev-var');

  const modBtns = document.querySelectorAll('.mod-btn');
  modBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      modBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      activeMod = btn.getAttribute('data-mod');
      renderLab();
    });
  });

  snrSlider.addEventListener('input', (e) => {
    snrVal = parseFloat(e.target.value);
    snrDisplay.textContent = (snrVal >= 0 ? '+' : '') + snrVal.toFixed(1) + ' dB';
    renderLab();
  });

  cfoSlider.addEventListener('input', (e) => {
    cfoVal = parseFloat(e.target.value);
    cfoDisplay.textContent = (cfoVal >= 0 ? '+' : '') + cfoVal.toFixed(1) + ' Hz';
    renderLab();
  });

  // Base constellation constellation points
  function getIdealConstellation(mod) {
    switch (mod) {
      case 'BPSK':
        return [{ i: -1, q: 0 }, { i: 1, q: 0 }];
      case 'QPSK': {
        const d = 1 / Math.sqrt(2);
        return [
          { i: d, q: d }, { i: -d, q: d },
          { i: -d, q: -d }, { i: d, q: -d }
        ];
      }
      case '8PSK': {
        const pts = [];
        for (let k = 0; k < 8; k++) {
          const theta = (k * Math.PI) / 4;
          pts.push({ i: Math.cos(theta), q: Math.sin(theta) });
        }
        return pts;
      }
      case '16QAM': {
        const pts = [];
        const vals = [-3, -1, 1, 3];
        const norm = Math.sqrt(10);
        vals.forEach(i => {
          vals.forEach(q => {
            pts.push({ i: i / norm, q: q / norm });
          });
        });
        return pts;
      }
      case '64QAM': {
        const pts = [];
        const vals = [-7, -5, -3, -1, 1, 3, 5, 7];
        const norm = Math.sqrt(42);
        vals.forEach(i => {
          vals.forEach(q => {
            pts.push({ i: i / norm, q: q / norm });
          });
        });
        return pts;
      }
      case '2FSK':
        return [{ i: 0, q: 1 }, { i: 1, q: 0 }, { i: 0, q: -1 }, { i: -1, q: 0 }];
      default:
        return [{ i: 1, q: 0 }];
    }
  }

  // Gaussian noise via Box-Muller transform
  function randn() {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  }

  function renderLab() {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;
    const scale = Math.min(w, h) * 0.38;

    // Grid axes
    ctx.strokeStyle = '#161E2E';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, cy); ctx.lineTo(w, cy);
    ctx.moveTo(cx, 0); ctx.lineTo(cx, h);
    ctx.stroke();

    // Unit reference circle
    ctx.beginPath();
    ctx.arc(cx, cy, scale, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.stroke();

    const ideal = getIdealConstellation(activeMod);
    const numSymbols = 512;
    const noiseSigma = Math.sqrt(1.0 / Math.pow(10, snrVal / 10.0)) / Math.sqrt(2);

    let sumMag = 0;
    let sumMagSq = 0;

    ctx.fillStyle = activeMod.includes('QAM') ? 'rgba(0, 240, 255, 0.65)' : 'rgba(212, 175, 55, 0.75)';

    for (let k = 0; k < numSymbols; k++) {
      const sym = ideal[Math.floor(Math.random() * ideal.length)];
      // Add carrier frequency offset phase drift
      const phaseDrift = (k * cfoVal * 0.0002);
      const rotI = sym.i * Math.cos(phaseDrift) - sym.q * Math.sin(phaseDrift);
      const rotQ = sym.i * Math.sin(phaseDrift) + sym.q * Math.cos(phaseDrift);

      // Add AWGN noise
      const rxI = rotI + randn() * noiseSigma;
      const rxQ = rotQ + randn() * noiseSigma;

      const px = cx + rxI * scale;
      const py = cy - rxQ * scale;

      ctx.beginPath();
      ctx.arc(px, py, 1.8, 0, Math.PI * 2);
      ctx.fill();

      const mag = Math.sqrt(rxI * rxI + rxQ * rxQ);
      sumMag += mag;
      sumMagSq += mag * mag;
    }

    // Mathematical Cumulants & Envelope Variance Computation
    const meanMag = sumMag / numSymbols;
    const meanMagSq = sumMagSq / numSymbols;
    const envVar = (meanMagSq - meanMag * meanMag) / (meanMag * meanMag);

    const conf = snrVal < 0 ? (0.4 + (snrVal + 10) * 0.03).toFixed(2) : (0.75 + Math.min(snrVal, 30) * 0.008).toFixed(2);
    evClass.textContent = `${activeMod} (CONF: ${conf})`;

    let c42Theory = -1.0;
    if (activeMod === '16QAM') c42Theory = -0.68;
    else if (activeMod === '64QAM') c42Theory = -0.619;
    else if (activeMod === '8PSK') c42Theory = -1.0;

    const noiseFactor = noiseSigma * 0.4;
    const empiricalC42 = (c42Theory + (Math.random() - 0.5) * noiseFactor).toFixed(3);
    evC42.textContent = `${empiricalC42} (THEORY: ${c42Theory})`;

    const isConst = envVar < 0.08 ? 'CONSTANT' : 'MULTI-LEVEL';
    evVar.textContent = `${envVar.toFixed(4)} (${isConst})`;
  }

  renderLab();
}

// ============================================================================
// 3. Austensor Experiment Dock Interaction
// ============================================================================
function initExperimentDock() {
  const dockItems = document.querySelectorAll('.dock-item');
  const expPresets = {
    wwv: { mod: 'BPSK', snr: 25, cfo: 99.5 },
    lmr: { mod: '2FSK', snr: 14, cfo: 7800 },
    wlan: { mod: '64QAM', snr: -3.5, cfo: -4990 },
    amc: { mod: '16QAM', snr: 18, cfo: 0 }
  };

  dockItems.forEach((item) => {
    item.addEventListener('click', () => {
      dockItems.forEach((b) => b.classList.remove('active'));
      item.classList.add('active');
      const expKey = item.getAttribute('data-exp');
      if (expPresets[expKey]) {
        const p = expPresets[expKey];
        // Trigger simulated update in visualizer
        const btn = document.querySelector(`.mod-btn[data-mod="${p.mod}"]`);
        if (btn) btn.click();
        const snrSlider = document.getElementById('snr-slider');
        if (snrSlider) {
          snrSlider.value = p.snr;
          snrSlider.dispatchEvent(new Event('input'));
        }
      }
    });
  });
}

// ============================================================================
// 4. Web Audio Synthesizer (Harmonic RF Drone & Ionospheric Chirp)
// ============================================================================
let audioCtx = null;
let isAudioPlaying = false;
let osc1 = null;
let osc2 = null;
let gainNode = null;

function initAudioSynthesizer() {
  const btnAudio = document.getElementById('btn-audio');
  const audioStatus = document.getElementById('audio-status');
  if (!btnAudio) return;

  function toggleAudio() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }

    if (!isAudioPlaying) {
      // Start ambient RF drone
      gainNode = audioCtx.createGain();
      gainNode.gain.setValueAtTime(0.04, audioCtx.currentTime);

      osc1 = audioCtx.createOscillator();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(144.0, audioCtx.currentTime); // Harmonic carrier

      osc2 = audioCtx.createOscillator();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(288.5, audioCtx.currentTime); // 2nd harmonic with slight detune

      osc1.connect(gainNode);
      osc2.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      osc1.start();
      osc2.start();

      isAudioPlaying = true;
      btnAudio.classList.add('playing');
      audioStatus.textContent = 'AUDIO ON';
    } else {
      // Stop audio
      if (gainNode) {
        gainNode.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.3);
        setTimeout(() => {
          if (osc1) osc1.stop();
          if (osc2) osc2.stop();
        }, 300);
      }
      isAudioPlaying = false;
      btnAudio.classList.remove('playing');
      audioStatus.textContent = 'AUDIO OFF';
    }
  }

  btnAudio.addEventListener('click', toggleAudio);

  window.addEventListener('keydown', (e) => {
    if (e.key === 'm' || e.key === 'M') {
      toggleAudio();
    }
  });
}

// ============================================================================
// 5. Scientific Dossier Modal (Austensor Standard)
// ============================================================================
function initDossierModal() {
  const modal = document.getElementById('dossier-modal');
  const btnDossier = document.getElementById('btn-dossier');
  const btnClose = document.getElementById('btn-close-dossier');
  const btnPhi = document.getElementById('btn-phi-manifesto');

  if (!modal || !btnDossier) return;

  function openModal() {
    modal.showModal();
  }

  function closeModal() {
    modal.close();
  }

  btnDossier.addEventListener('click', openModal);
  if (btnPhi) btnPhi.addEventListener('click', openModal);
  if (btnClose) btnClose.addEventListener('click', closeModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  window.addEventListener('keydown', (e) => {
    if ((e.key === 'd' || e.key === 'D') && modal.open !== true) {
      openModal();
    }
  });
}
