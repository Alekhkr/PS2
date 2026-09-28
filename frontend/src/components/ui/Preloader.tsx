import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface PreloaderProps {
  onComplete: () => void;
}

export const Preloader: React.FC<PreloaderProps> = ({ onComplete }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(onComplete, 400);
          return 100;
        }
        const step = Math.floor(Math.random() * 8) + 4;
        return Math.min(100, prev + step);
      });
    }, 35);

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <AnimatePresence>
      {progress < 100 && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }}
          className="fixed inset-0 z-50 flex flex-col justify-between p-8 md:p-16 bg-[#000000] text-white select-none pointer-events-none"
        >
          {/* Top Identifier */}
          <div className="flex justify-between items-center font-mono text-xs text-[#888888]">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#00f0ff] animate-ping" />
              <span>AUSTENSOR // SYSTEM INITIALIZATION</span>
            </div>
            <div>EXP_07 // HARMONIC TENSOR WAVEFIELD</div>
          </div>

          {/* Central Counter */}
          <div className="flex flex-col items-center">
            <span className="font-mono text-7xl md:text-9xl font-extralight tracking-tighter text-white">
              {progress.toString().padStart(3, '0')}
              <span className="text-2xl md:text-3xl text-[#00f0ff] font-light ml-1">%</span>
            </span>
            <span className="font-mono text-xs tracking-[0.3em] uppercase text-[#888888] mt-4">
              Synthesizing 15-Band Parametric Ribbons
            </span>
          </div>

          {/* Bottom Progress Line */}
          <div className="w-full">
            <div className="w-full h-px bg-white/10 relative overflow-hidden">
              <motion.div
                className="absolute top-0 left-0 bottom-0 bg-[#00f0ff] shadow-[0_0_12px_#00f0ff]"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between font-mono text-[10px] text-[#666666] mt-2">
              <span>GLSL SHADER COMPILATION</span>
              <span>FOURIER SPATIAL CONTINUUM</span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
