import React from 'react';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';

interface ScenePostProcessingProps {
  bloomIntensity?: number;
}

export const ScenePostProcessing: React.FC<ScenePostProcessingProps> = ({
  bloomIntensity = 1.4,
}) => {
  return (
    <EffectComposer multisampling={4}>
      <Bloom
        luminanceThreshold={0.18}
        luminanceSmoothing={0.9}
        intensity={bloomIntensity}
        mipmapBlur
      />
      <Vignette eskil={false} offset={0.15} darkness={0.85} />
    </EffectComposer>
  );
};
