import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface WaveRibbonSceneProps {
  snrDb?: number;
  modulationName?: string;
  isAudioActive?: boolean;
}

export const WaveRibbonScene: React.FC<WaveRibbonSceneProps> = ({
  snrDb = 24.5,
  modulationName = 'BPSK',
  isAudioActive = false,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0, isDown: false, prevX: 0, prevY: 0 });
  const rotRef = useRef({ x: 0.15, y: -0.25, targetX: 0.15, targetY: -0.25 });

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x03070d, 0.035);

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 4.5, 16);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
    scene.add(ambientLight);

    const cyanPointLight = new THREE.PointLight(0x00f0ff, 2.5, 30);
    cyanPointLight.position.set(-8, 6, 5);
    scene.add(cyanPointLight);

    const violetPointLight = new THREE.PointLight(0x9d4edd, 2.5, 30);
    violetPointLight.position.set(8, -4, 5);
    scene.add(violetPointLight);

    // 3. Grid Floor reflection
    const gridHelper = new THREE.GridHelper(30, 30, 0x1e293b, 0x0a1120);
    gridHelper.position.y = -4;
    scene.add(gridHelper);

    // 4. Background Dust Particles
    const particleCount = 400;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePos[i] = (Math.random() - 0.5) * 36;
      particlePos[i + 1] = (Math.random() - 0.5) * 20;
      particlePos[i + 2] = (Math.random() - 0.5) * 30;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 0.06,
      color: 0x00f0ff,
      transparent: true,
      opacity: 0.4,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 5. 15 Harmonic Ribbons
    const numRibbons = 15;
    const pointsPerRibbon = 120;
    const xMin = -14;
    const xMax = 14;
    const ribbonGroup = new THREE.Group();
    scene.add(ribbonGroup);

    const ribbons: {
      mesh: THREE.Mesh;
      positions: Float32Array;
      geometry: THREE.BufferGeometry;
      baseZ: number;
      freqOffset: number;
    }[] = [];

    // Spectral Chrominance Palette
    const palette = [
      new THREE.Color(0x00f0ff), // Cyan
      new THREE.Color(0x38bdf8), // Light Blue
      new THREE.Color(0x6366f1), // Indigo
      new THREE.Color(0x8b5cf6), // Purple
      new THREE.Color(0xa855f7), // Violet
      new THREE.Color(0xd946ef), // Magenta
      new THREE.Color(0xf43f5e), // Rose
      new THREE.Color(0xf59e0b), // Amber
      new THREE.Color(0x10b981), // Emerald
      new THREE.Color(0x06b6d4), // Deep Cyan
    ];

    for (let r = 0; r < numRibbons; r++) {
      const z = (r - (numRibbons - 1) / 2) * 0.75;
      const vertexCount = pointsPerRibbon * 2;
      const posArray = new Float32Array(vertexCount * 3);
      const indices: number[] = [];

      for (let i = 0; i < pointsPerRibbon - 1; i++) {
        const top1 = i * 2;
        const bot1 = i * 2 + 1;
        const top2 = (i + 1) * 2;
        const bot2 = (i + 1) * 2 + 1;

        indices.push(top1, bot1, top2);
        indices.push(bot1, bot2, top2);
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
      geometry.setIndex(indices);

      const colorIdx = r % palette.length;
      const ribbonColor = palette[colorIdx];

      const material = new THREE.MeshStandardMaterial({
        color: ribbonColor,
        roughness: 0.2,
        metalness: 0.8,
        emissive: ribbonColor,
        emissiveIntensity: 0.35,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.88,
        wireframe: false,
      });

      const mesh = new THREE.Mesh(geometry, material);
      ribbonGroup.add(mesh);

      ribbons.push({
        mesh,
        positions: posArray,
        geometry,
        baseZ: z,
        freqOffset: r * 0.24,
      });
    }

    // 6. Interaction Listeners
    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mouseRef.current.targetX = normX;
      mouseRef.current.targetY = normY;

      if (mouseRef.current.isDown) {
        const deltaX = e.clientX - mouseRef.current.prevX;
        const deltaY = e.clientY - mouseRef.current.prevY;
        rotRef.current.targetY += deltaX * 0.005;
        rotRef.current.targetX += deltaY * 0.005;
        mouseRef.current.prevX = e.clientX;
        mouseRef.current.prevY = e.clientY;
      }
    };

    const handleMouseDown = (e: MouseEvent) => {
      mouseRef.current.isDown = true;
      mouseRef.current.prevX = e.clientX;
      mouseRef.current.prevY = e.clientY;
    };

    const handleMouseUp = () => {
      mouseRef.current.isDown = false;
    };

    const handleWheel = (e: WheelEvent) => {
      camera.position.z = Math.min(24, Math.max(8, camera.position.z + e.deltaY * 0.01));
    };

    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mouseup', handleMouseUp);
    container.addEventListener('wheel', handleWheel, { passive: true });

    // 7. Animation Loop
    let animId = 0;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Inertial camera rotation
      rotRef.current.x += (rotRef.current.targetX - rotRef.current.x) * 0.08;
      rotRef.current.y += (rotRef.current.targetY - rotRef.current.y) * 0.08;

      ribbonGroup.rotation.x = rotRef.current.x;
      ribbonGroup.rotation.y = rotRef.current.y + Math.sin(elapsedTime * 0.15) * 0.05;

      // Mouse smoothing
      mouseRef.current.x += (mouseRef.current.targetX - mouseRef.current.x) * 0.05;
      mouseRef.current.y += (mouseRef.current.targetY - mouseRef.current.y) * 0.05;

      const audioMod = isAudioActive ? 1.4 : 1.0;
      const speed = 1.2 * audioMod;

      // Update Ribbon Wavefield Superposition
      for (let r = 0; r < ribbons.length; r++) {
        const { positions, geometry, baseZ, freqOffset } = ribbons[r];
        let pIdx = 0;

        for (let i = 0; i < pointsPerRibbon; i++) {
          const t = i / (pointsPerRibbon - 1);
          const x = xMin + t * (xMax - xMin);

          // Spatial damping envelope: exp(-alpha * x^2)
          const damping = Math.exp(-0.015 * x * x);

          // Multi-harmonic sine superposition
          const wave1 = 1.1 * Math.sin(0.45 * x + elapsedTime * speed + freqOffset);
          const wave2 = 0.5 * Math.sin(1.1 * x - elapsedTime * 0.7 * speed + freqOffset * 1.5);
          const wave3 = 0.25 * Math.sin(2.3 * x + elapsedTime * 1.4 * speed);

          // Interactive cursor ripple
          const cursorDist = Math.hypot(x - mouseRef.current.x * 10, baseZ - mouseRef.current.y * 5);
          const cursorRipple = Math.exp(-0.4 * cursorDist) * Math.sin(cursorDist * 2.5 - elapsedTime * 4.0) * 0.9;

          const y = (wave1 + wave2 + wave3 + cursorRipple) * damping;

          // Top vertex
          positions[pIdx] = x;
          positions[pIdx + 1] = y + 0.12;
          positions[pIdx + 2] = baseZ;

          // Bottom vertex
          positions[pIdx + 3] = x;
          positions[pIdx + 4] = y - 0.12;
          positions[pIdx + 5] = baseZ;

          pIdx += 6;
        }

        geometry.attributes.position.needsUpdate = true;
        geometry.computeVertexNormals();
      }

      // Rotate particle dust
      particles.rotation.y = elapsedTime * 0.02;

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      container.removeEventListener('wheel', handleWheel);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [isAudioActive]);

  return (
    <div className="relative w-full h-full overflow-hidden select-none">
      <div ref={mountRef} className="absolute inset-0 cursor-grab active:cursor-grabbing" />

      {/* Austensor Page 7 Floating Experiment Overlay Info */}
      <div className="absolute top-6 left-8 pointer-events-none z-10">
        <div className="flex items-center gap-3 mb-1">
          <span className="font-mono text-[10px] tracking-[0.25em] text-[#00f0ff] uppercase px-2 py-0.5 rounded bg-[rgba(0,240,255,0.08)] border border-[rgba(0,240,255,0.25)]">
            EXP_07 // WAVE OSCILLATION
          </span>
          <span className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400">
            <span className="pulse-emerald" /> 60 FPS GPU
          </span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white font-['Syne'] uppercase">
          Harmonic Tensor Wavefield
        </h1>
        <p className="text-xs text-slate-400 max-w-md mt-1 font-sans leading-relaxed">
          15-band multi-frequency spatial continuum. Parametric extruded ribbon manifold with
          sub-sample phase interference, localized damping, and spectral chrominance.
        </p>
      </div>

      {/* Floating Telemetry Badges */}
      <div className="absolute top-6 right-8 pointer-events-none z-10 flex gap-3">
        <div className="austensor-panel px-3.5 py-2 text-right">
          <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">MODULATION</div>
          <div className="text-sm font-mono font-bold text-[#00f0ff]">{modulationName}</div>
        </div>
        <div className="austensor-panel px-3.5 py-2 text-right">
          <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">IN-BAND SNR</div>
          <div className="text-sm font-mono font-bold text-emerald-400">{snrDb.toFixed(1)} dB</div>
        </div>
      </div>
    </div>
  );
};
