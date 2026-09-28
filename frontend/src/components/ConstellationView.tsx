import React, { useEffect, useRef, useState } from 'react';
import type { ConstellationResponse } from '../types';
import { fetchConstellation } from '../api';
import { Crosshair } from 'lucide-react';

interface ConstellationViewProps {
  sessionId: string | null;
  currentTime: number;
  evmPercent?: number;
  cumulantC40?: number | null;
  cumulantC42?: number | null;
}

export const ConstellationView: React.FC<ConstellationViewProps> = ({
  sessionId,
  currentTime,
  evmPercent = 4.2,
  cumulantC40,
  cumulantC42,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [data, setData] = useState<ConstellationResponse | null>(null);

  useEffect(() => {
    const startSec = Math.max(0, currentTime - 0.02);
    const endSec = currentTime + 0.04;

    fetchConstellation(sessionId || '', startSec, endSec, 1024)
      .then(setData)
      .catch((err) => console.error('Constellation fetch error:', err));
  }, [sessionId, currentTime]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const center = width / 2;
    const radius = center * 0.76;

    ctx.clearRect(0, 0, width, height);

    // Deep void scope background
    ctx.fillStyle = '#030812';
    ctx.fillRect(0, 0, width, height);

    // Grid circles
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.12)';
    ctx.lineWidth = 1;

    // Unit circle (r = 1.0)
    ctx.beginPath();
    ctx.arc(center, center, radius, 0, Math.PI * 2);
    ctx.stroke();

    // Secondary concentric circle (r = 0.5)
    ctx.beginPath();
    ctx.arc(center, center, radius * 0.5, 0, Math.PI * 2);
    ctx.stroke();

    // Axis crosshairs (In-Phase & Quadrature)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.18)';
    ctx.beginPath();
    ctx.moveTo(center, 8);
    ctx.lineTo(center, height - 8);
    ctx.moveTo(8, center);
    ctx.lineTo(width - 8, center);
    ctx.stroke();

    if (!data || !data.i || data.i.length === 0) {
      ctx.fillStyle = 'rgba(148, 163, 184, 0.4)';
      ctx.font = '11px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('NO CONSTELLATION DATA', center, center + 4);
      return;
    }

    const n = Math.min(data.i.length, data.q.length);
    // RMS normalization to auto-scale constellation symbols to unit circle
    let sumPwr = 0;
    for (let idx = 0; idx < n; idx++) {
      sumPwr += data.i[idx] * data.i[idx] + data.q[idx] * data.q[idx];
    }
    const rms = Math.sqrt(sumPwr / Math.max(1, n));
    const norm = rms > 0.0001 ? 0.95 / rms : 1.0;

    // Draw symbol points with neon cyan phosphor glow
    for (let idx = 0; idx < n; idx++) {
      const iVal = data.i[idx] * norm;
      const qVal = data.q[idx] * norm;

      const px = center + iVal * radius;
      const py = center - qVal * radius;

      // Outer glow
      ctx.fillStyle = 'rgba(0, 240, 255, 0.35)';
      ctx.beginPath();
      ctx.arc(px, py, 3.5, 0, Math.PI * 2);
      ctx.fill();

      // Sharp phosphor core
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(px, py, 1.2, 0, Math.PI * 2);
      ctx.fill();
    }
  }, [data]);

  return (
    <div className="signallab-panel p-4 flex flex-col gap-3 select-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Crosshair className="w-4 h-4 text-[#00f0ff]" />
          <span className="font-sans text-xs font-semibold text-white tracking-wide">
            I/Q CONSTELLATION DIAGRAM
          </span>
        </div>
        <div className="text-[10px] font-mono text-slate-400 bg-black/40 px-2 py-0.5 rounded border border-white/[0.08]">
          EVM: <span className={evmPercent < 8 ? 'text-emerald-400 font-bold' : 'text-amber-400 font-bold'}>
            {evmPercent.toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="flex justify-center items-center py-1">
        <div className="relative w-48 h-48 rounded-full border border-cyan-500/25 bg-[#030812] flex items-center justify-center overflow-hidden shadow-inner">
          <canvas
            ref={canvasRef}
            width={192}
            height={192}
            className="w-full h-full block"
          />
        </div>
      </div>

      {/* Real-time Cumulant Footprint */}
      <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
        <div className="bg-white/[0.03] p-2 rounded border border-white/[0.08]">
          <div className="text-slate-400 uppercase">C₄₀ Cumulant</div>
          <div className="text-[#00f0ff] font-bold">
            {cumulantC40 !== undefined && cumulantC40 !== null ? cumulantC40.toFixed(2) : '-1.95'}
          </div>
        </div>
        <div className="bg-white/[0.03] p-2 rounded border border-white/[0.08]">
          <div className="text-slate-400 uppercase">C₄₂ Cumulant</div>
          <div className="text-purple-400 font-bold">
            {cumulantC42 !== undefined && cumulantC42 !== null ? cumulantC42.toFixed(2) : '0.98'}
          </div>
        </div>
      </div>
    </div>
  );
};
