import { useRef, useMemo, useCallback } from 'react';
import * as THREE from 'three';

export interface WaveShaderUniforms {
  [key: string]: THREE.IUniform;
  uTime: { value: number };
  uSpeed: { value: number };
  uAudioLevel: { value: number };
  uScrollProgress: { value: number };
  uPointer: { value: THREE.Vector2 };
  uPointerIntensity: { value: number };
  uRibbonIndex: { value: number };
  uColorA: { value: THREE.Color };
  uColorB: { value: THREE.Color };
  uColorC: { value: THREE.Color };
  uColorD: { value: THREE.Color };
}

export function useWaveShader(audioLevel: number = 0, scrollProgress: number = 0) {
  const pointerTarget = useRef(new THREE.Vector2(0, 0));
  const pointerCurrent = useRef(new THREE.Vector2(0, 0));
  const pointerActive = useRef(0);

  // Spectral Chrominance Palette matching Austensor Page 7
  const colors = useMemo(() => ({
    colorA: new THREE.Color('#00f0ff'), // Electric Cyan
    colorB: new THREE.Color('#8a2be2'), // Laser Violet
    colorC: new THREE.Color('#ffaa00'), // Hot Amber
    colorD: new THREE.Color('#00ff88'), // Radiant Emerald
  }), []);

  const createUniforms = useCallback((ribbonIndex: number): WaveShaderUniforms => {
    return {
      uTime: { value: 0 },
      uSpeed: { value: 1.15 },
      uAudioLevel: { value: 0 },
      uScrollProgress: { value: 0 },
      uPointer: { value: new THREE.Vector2(0, 0) },
      uPointerIntensity: { value: 0 },
      uRibbonIndex: { value: ribbonIndex },
      uColorA: { value: colors.colorA },
      uColorB: { value: colors.colorB },
      uColorC: { value: colors.colorC },
      uColorD: { value: colors.colorD },
    };
  }, [colors]);

  const onPointerMove = useCallback((e: MouseEvent | React.PointerEvent) => {
    const x = (e.clientX / window.innerWidth) * 2 - 1;
    const y = -(e.clientY / window.innerHeight) * 2 + 1;
    pointerTarget.current.set(x, y);
    pointerActive.current = 1.0;
  }, []);

  const onPointerLeave = useCallback(() => {
    pointerActive.current = 0.0;
  }, []);

  const updateUniforms = useCallback(
    (uniformsList: WaveShaderUniforms[], _clockDelta: number, elapsedTime: number) => {
      // Smooth pointer interpolation
      pointerCurrent.current.lerp(pointerTarget.current, 0.08);

      uniformsList.forEach((u) => {
        u.uTime.value = elapsedTime;
        u.uAudioLevel.value = THREE.MathUtils.lerp(u.uAudioLevel.value, audioLevel, 0.12);
        u.uScrollProgress.value = scrollProgress;
        u.uPointer.value.copy(pointerCurrent.current);
        u.uPointerIntensity.value = THREE.MathUtils.lerp(
          u.uPointerIntensity.value,
          pointerActive.current,
          0.05
        );
      });
    },
    [audioLevel, scrollProgress]
  );

  return {
    createUniforms,
    updateUniforms,
    onPointerMove,
    onPointerLeave,
  };
}
