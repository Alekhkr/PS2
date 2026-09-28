import React, { useEffect, useRef, useState } from 'react';
import { Waves } from 'lucide-react';
import { fetchSpectrogram } from '../api';
import type { SpectrogramResponse } from '../types';

interface SpectrogramViewProps {
  sessionId: string | null;
  sampleRate: number;
  centerFreq: number;
}

// Colormap lookup: Viridis / Electric Spectrum (-80 dB to 0 dB)
function dbToRgb(db: number): [number, number, number] {
  // Normalize -80 dB ... 0 dB -> [0, 1]
  const t = Math.max(0, Math.min(1, (db + 80) / 80));
  
  if (t < 0.25) {
    // Deep blue to cyan
    const f = t / 0.25;
    return [Math.floor(10 * (1 - f) + 0 * f), Math.floor(15 * (1 - f) + 200 * f), Math.floor(40 * (1 - f) + 255 * f)];
  } else if (t < 0.5) {
    // Cyan to emerald
    const f = (t - 0.25) / 0.25;
    return [0, Math.floor(200 * (1 - f) + 240 * f), Math.floor(255 * (1 - f) + 120 * f)];
  } else if (t < 0.75) {
    // Emerald to bright amber/yellow
    const f = (t - 0.5) / 0.25;
    return [Math.floor(245 * f), Math.floor(240 * (1 - f) + 220 * f), Math.floor(120 * (1 - f) + 20 * f)];
  } else {
    // Yellow to pure white
    const f = (t - 0.75) / 0.25;
    return [255, Math.floor(220 + 35 * f), Math.floor(20 + 235 * f)];
  }
}

export const SpectrogramView: React.FC<SpectrogramViewProps> = ({
  sessionId,
  sampleRate,
  centerFreq,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [specData, setSpecData] = useState<SpectrogramResponse | null>(null);
  const [nFft, setNFft] = useState<number>(512);

  useEffect(() => {
    fetchSpectrogram(sessionId || undefined, 0.0, 0.2, nFft)
      .then((data) => setSpecData(data))
      .catch((err) => console.error('Failed to load spectrogram:', err));
  }, [sessionId, nFft]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    if (!specData || !specData.magnitude_db || specData.magnitude_db.length === 0) {
      ctx.fillStyle = '#030812';
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = 'rgba(148, 163, 184, 0.4)';
      ctx.font = '11px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('COMPUTING 2D STFT WATERFALL...', width / 2, height / 2);
      return;
    }

    const nFreqBins = specData.magnitude_db.length;
    const nTimeSteps = specData.magnitude_db[0].length;

    // Render STFT spectrogram matrix
    const imgData = ctx.createImageData(width, height);
    const data = imgData.data;

    for (let y = 0; y < height; y++) {
      // Invert Y so high frequencies are at the top
      const freqIdx = Math.floor(((height - 1 - y) / height) * nFreqBins);
      const row = specData.magnitude_db[Math.min(nFreqBins - 1, Math.max(0, freqIdx))];

      for (let x = 0; x < width; x++) {
        const timeIdx = Math.floor((x / width) * nTimeSteps);
        const db = row[Math.min(nTimeSteps - 1, Math.max(0, timeIdx))] ?? -80;
        const [r, g, b] = dbToRgb(db);

        const pixelIdx = (y * width + x) * 4;
        data[pixelIdx] = r;
        data[pixelIdx + 1] = g;
        data[pixelIdx + 2] = b;
        data[pixelIdx + 3] = 240;
      }
    }

    ctx.putImageData(imgData, 0, 0);

    // Overlay center frequency reticle line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
    ctx.setLineDash([]);
  }, [specData]);

  const spanKhz = sampleRate > 0 ? (sampleRate / 2e3).toFixed(1) : '10.0';

  return (
    <div className="signallab-panel p-4 flex flex-col gap-2 select-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Waves className="w-4 h-4 text-purple-400" />
          <span className="font-sans text-xs font-semibold text-white tracking-wide">
            2D TIME-FREQUENCY WATERFALL (STFT)
          </span>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-[10px] font-mono bg-white/[0.04] p-0.5 rounded border border-white/[0.08]">
            {[256, 512, 1024].map((fft) => (
              <button
                key={fft}
                onClick={() => setNFft(fft)}
                className={`px-1.5 py-0.5 rounded ${nFft === fft ? 'bg-purple-500 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                {fft}
              </button>
            ))}
          </div>

          <div className="text-[10px] font-mono text-slate-400 bg-black/40 px-2 py-0.5 rounded border border-white/[0.08]">
            SPAN: <span className="text-purple-300 font-bold">±{spanKhz} kHz</span>
          </div>
        </div>
      </div>

      <div className="relative w-full h-36 rounded-lg bg-[#030812] border border-white/[0.08] overflow-hidden shadow-inner">
        <canvas
          ref={canvasRef}
          width={600}
          height={144}
          className="w-full h-full block"
        />
        <div className="absolute top-1 left-2 text-[9px] font-mono text-cyan-300 bg-black/60 px-1.5 py-0.5 rounded backdrop-blur">
          +{spanKhz} kHz
        </div>
        <div className="absolute bottom-1 left-2 text-[9px] font-mono text-cyan-300 bg-black/60 px-1.5 py-0.5 rounded backdrop-blur">
          -{spanKhz} kHz
        </div>
        <div className="absolute top-1 right-2 text-[9px] font-mono text-amber-400 bg-black/60 px-1.5 py-0.5 rounded backdrop-blur">
          f₀: {(centerFreq / 1e6).toFixed(3)} MHz
        </div>
      </div>
    </div>
  );
};
