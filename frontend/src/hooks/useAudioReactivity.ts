import { useState, useEffect, useRef, useCallback } from 'react';

export function useAudioReactivity() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [eqLevels, setEqLevels] = useState<number[]>([0.1, 0.2, 0.15, 0.3, 0.25, 0.4, 0.2, 0.3]);

  const ctxRef = useRef<AudioContext | null>(null);
  const masterGainRef = useRef<GainNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const oscillatorsRef = useRef<OscillatorNode[]>([]);

  const initContext = useCallback(() => {
    if (ctxRef.current) return;
    const AudioCtx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new AudioCtx();
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, ctx.currentTime);

    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;

    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(550, ctx.currentTime);
    filter.Q.setValueAtTime(3.5, ctx.currentTime);

    gain.connect(filter);
    filter.connect(analyser);
    analyser.connect(ctx.destination);

    ctxRef.current = ctx;
    masterGainRef.current = gain;
    analyserRef.current = analyser;
  }, []);

  const toggle = useCallback(() => {
    initContext();
    const ctx = ctxRef.current;
    const gain = masterGainRef.current;
    if (!ctx || !gain) return;

    if (ctx.state === 'suspended') {
      ctx.resume();
    }

    if (isPlaying) {
      // Fade out
      gain.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.08);
      setTimeout(() => {
        oscillatorsRef.current.forEach((osc) => {
          try {
            osc.stop();
            osc.disconnect();
          } catch {
            // Ignore
          }
        });
        oscillatorsRef.current = [];
        setIsPlaying(false);
      }, 120);
    } else {
      // Start harmonic drone: 55Hz (A1), 110Hz, 165Hz, 220Hz, 330Hz
      const freqs = [55.0, 110.0, 165.0, 220.0, 330.0];
      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const oscGain = ctx.createGain();
        osc.type = idx % 2 === 0 ? 'sine' : 'triangle';
        osc.frequency.setValueAtTime(freq + idx * 0.4, ctx.currentTime);

        const amp = 0.35 / (idx + 1);
        oscGain.gain.setValueAtTime(amp, ctx.currentTime);

        osc.connect(oscGain);
        oscGain.connect(gain);
        osc.start();
        oscillatorsRef.current.push(osc);
      });

      gain.gain.setTargetAtTime(0.18, ctx.currentTime, 0.1);
      setIsPlaying(true);
    }
  }, [isPlaying, initContext]);

  // Animation frame loop for extracting RMS audio level
  useEffect(() => {
    let animId = 0;
    const buffer = new Uint8Array(32);

    const updateAudio = () => {
      if (analyserRef.current && isPlaying) {
        analyserRef.current.getByteFrequencyData(buffer);
        let sum = 0;
        const eq: number[] = [];
        for (let i = 0; i < 8; i++) {
          const val = buffer[i * 2] / 255;
          sum += val;
          eq.push(val);
        }
        setAudioLevel(sum / 8);
        setEqLevels(eq);
      } else {
        setAudioLevel((prev) => Math.max(0, prev * 0.95));
      }
      animId = requestAnimationFrame(updateAudio);
    };

    animId = requestAnimationFrame(updateAudio);
    return () => cancelAnimationFrame(animId);
  }, [isPlaying]);

  return { isPlaying, audioLevel, eqLevels, toggle };
}
