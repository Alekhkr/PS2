import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { waveRibbonVertexShader } from '../../shaders/waveRibbon.vert.glsl';
import { waveRibbonFragmentShader } from '../../shaders/waveRibbon.frag.glsl';
import { useWaveShader, type WaveShaderUniforms } from '../../hooks/useWaveShader';

interface WaveRibbonsProps {
  audioLevel?: number;
  scrollProgress?: number;
}

export const WaveRibbons: React.FC<WaveRibbonsProps> = ({
  audioLevel = 0,
  scrollProgress = 0,
}) => {
  const numRibbons = 15;
  const pointsPerRibbon = 140;
  const xMin = -16.0;
  const xMax = 16.0;

  const { createUniforms, updateUniforms } = useWaveShader(audioLevel, scrollProgress);
  const uniformsListRef = useRef<WaveShaderUniforms[]>([]);

  // Create ribbon quad strip geometries and materials
  const ribbons = useMemo(() => {
    const list: {
      geometry: THREE.BufferGeometry;
      material: THREE.ShaderMaterial;
      uniforms: WaveShaderUniforms;
    }[] = [];

    const newUniforms: WaveShaderUniforms[] = [];

    for (let r = 0; r < numRibbons; r++) {
      const zOffset = (r - (numRibbons - 1) / 2) * 0.72;
      const vertexCount = pointsPerRibbon * 2;
      const posArray = new Float32Array(vertexCount * 3);
      const uvArray = new Float32Array(vertexCount * 2);
      const indices: number[] = [];

      let vIdx = 0;
      let uvIdx = 0;

      for (let i = 0; i < pointsPerRibbon; i++) {
        const t = i / (pointsPerRibbon - 1);
        const x = xMin + t * (xMax - xMin);

        // Top vertex (+0.14 width)
        posArray[vIdx] = x;
        posArray[vIdx + 1] = 0;
        posArray[vIdx + 2] = zOffset + 0.14;

        uvArray[uvIdx] = t;
        uvArray[uvIdx + 1] = 1.0;

        // Bottom vertex (-0.14 width)
        posArray[vIdx + 3] = x;
        posArray[vIdx + 4] = 0;
        posArray[vIdx + 5] = zOffset - 0.14;

        uvArray[uvIdx + 2] = t;
        uvArray[uvIdx + 3] = 0.0;

        vIdx += 6;
        uvIdx += 4;

        if (i < pointsPerRibbon - 1) {
          const top1 = i * 2;
          const bot1 = i * 2 + 1;
          const top2 = (i + 1) * 2;
          const bot2 = (i + 1) * 2 + 1;

          indices.push(top1, bot1, top2);
          indices.push(bot1, bot2, top2);
        }
      }

      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
      geometry.setAttribute('uv', new THREE.BufferAttribute(uvArray, 2));
      geometry.setIndex(indices);
      geometry.computeVertexNormals();

      const uniforms = createUniforms(r);
      newUniforms.push(uniforms);

      const material = new THREE.ShaderMaterial({
        vertexShader: waveRibbonVertexShader,
        fragmentShader: waveRibbonFragmentShader,
        uniforms,
        side: THREE.DoubleSide,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      list.push({ geometry, material, uniforms });
    }

    uniformsListRef.current = newUniforms;
    return list;
  }, [createUniforms]);

  // Per-frame GLSL uniforms animation
  useFrame((state, delta) => {
    updateUniforms(uniformsListRef.current, delta, state.clock.getElapsedTime());
  });

  return (
    <group position={[0, 0.4, 0]}>
      {ribbons.map((ribbon, idx) => (
        <mesh
          key={idx}
          geometry={ribbon.geometry}
          material={ribbon.material}
        />
      ))}
    </group>
  );
};
