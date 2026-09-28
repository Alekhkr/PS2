import React, { useRef, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { WaveRibbons } from './WaveRibbons';
import { ScenePostProcessing } from './ScenePostProcessing';

interface CanvasContainerProps {
  isVisible?: boolean;
  audioLevel?: number;
  scrollProgress?: number;
  onPointerMove?: (e: React.PointerEvent) => void;
}

function BackgroundParticles() {
  const count = 450;
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i += 3) {
      pos[i] = (Math.random() - 0.5) * 44;
      pos[i + 1] = (Math.random() - 0.5) * 24;
      pos[i + 2] = (Math.random() - 0.5) * 32;
    }
    return pos;
  }, []);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.055}
        color="#00f0ff"
        transparent
        opacity={0.35}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

export const CanvasContainer: React.FC<CanvasContainerProps> = ({
  isVisible = true,
  audioLevel = 0,
  scrollProgress = 0,
  onPointerMove,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  if (!isVisible) {
    return <div className="fixed inset-0 w-screen h-screen z-0 bg-[#03070d]" />;
  }

  return (
    <div
      ref={containerRef}
      onPointerMove={onPointerMove}
      className="fixed inset-0 w-screen h-screen z-0 pointer-events-none bg-[#03070d]"
    >
      <div className="absolute inset-0 z-10 pointer-events-none bg-gradient-to-b from-transparent via-[#03070d]/50 to-[#03070d]" />
      <Canvas
        camera={{ position: [0, 4.8, 15.5], fov: 46, near: 0.1, far: 100 }}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: 'high-performance',
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1.15,
        }}
        dpr={[1, 2]}
      >
        <color attach="background" args={['#000000']} />
        <fogExp2 attach="fog" args={['#000000', 0.032]} />

        {/* Ambient & Point Lighting */}
        <ambientLight intensity={0.4} />
        <pointLight position={[-10, 8, 8]} color="#00f0ff" intensity={2.2} distance={35} />
        <pointLight position={[10, -5, 6]} color="#8a2be2" intensity={2.2} distance={35} />

        {/* 15 Parametric Extruded Ribbon Tubes */}
        <WaveRibbons audioLevel={audioLevel} scrollProgress={scrollProgress} />

        {/* Background Star Particles */}
        <BackgroundParticles />

        {/* Floor Grid Reflection */}
        <gridHelper
          args={[36, 36, '#1e293b', '#080d18']}
          position={[0, -4.2, 0]}
        />

        {/* Orbit Controls with Silky Inertia */}
        <OrbitControls
          enableZoom={false}
          enablePan={false}
          rotateSpeed={0.45}
          dampingFactor={0.06}
          minPolarAngle={Math.PI / 3.8}
          maxPolarAngle={Math.PI / 1.9}
        />

        {/* Post-Processing Selective Bloom */}
        <ScenePostProcessing bloomIntensity={1.5 + audioLevel * 1.0} />
      </Canvas>
    </div>
  );
};
