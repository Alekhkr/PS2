import React, { useEffect, useRef, useState, useCallback } from 'react';
import type { WaveformLodResponse } from '../types';
import { fetchWaveformLod } from '../api';
import { Play, Pause, RotateCcw, Activity } from 'lucide-react';

interface SmoothWaveformProps {
  sessionId: string | null;
  totalDuration: number;
  sampleRate: number;
  currentTime: number;
  onTimeChange: (time: number) => void;
}

export const SmoothWaveform: React.FC<SmoothWaveformProps> = ({
  sessionId,
  totalDuration,
  sampleRate,
  currentTime,
  onTimeChange,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const minimapRef = useRef<HTMLCanvasElement>(null);

  // Viewport time state (startSec, endSec)
  const [viewport, setViewport] = useState<{ start: number; end: number }>({
    start: 0,
    end: Math.min(0.05, totalDuration || 0.05),
  });

  const [waveData, setWaveData] = useState<WaveformLodResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showI, setShowI] = useState(true);
  const [showQ, setShowQ] = useState(true);
  const [autoGain, setAutoGain] = useState(true);
  const [gainMultiplier, setGainMultiplier] = useState(1.0);
  const [isLiveSweep, setIsLiveSweep] = useState(true);
  const sweepSpeed = 1.0; // 1x real-time factor
  const [hoverInfo, setHoverInfo] = useState<{ time: number; ampI: number; ampQ: number } | null>(null);

  // Dragging state
  const isDraggingRef = useRef(false);
  const dragStartXRef = useRef(0);
  const dragStartViewportRef = useRef({ start: 0, end: 0 });

  // Reset viewport when duration or session changes
  useEffect(() => {
    if (totalDuration > 0) {
      setViewport({
        start: 0,
        end: Math.min(0.05, totalDuration),
      });
    }
  }, [totalDuration, sessionId]);

  // Fetch LOD waveform data
  const loadWaveformData = useCallback(async (start: number, end: number) => {
    try {
      setLoading(true);
      const data = await fetchWaveformLod(sessionId || '', start, end, 1200);
      setWaveData(data);
    } catch (err) {
      console.error('Failed to load waveform LOD:', err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Debounced load
  const fetchTimeoutRef = useRef<number | null>(null);
  useEffect(() => {
    if (fetchTimeoutRef.current) clearTimeout(fetchTimeoutRef.current);
    fetchTimeoutRef.current = window.setTimeout(() => {
      loadWaveformData(viewport.start, viewport.end);
    }, 30);

    return () => {
      if (fetchTimeoutRef.current) clearTimeout(fetchTimeoutRef.current);
    };
  }, [sessionId, viewport.start, viewport.end, loadWaveformData]);

  // Live Sweep Animation Engine
  useEffect(() => {
    if (!isLiveSweep) return;

    let animFrameId: number;
    let lastTimestamp = performance.now();

    const sweepStep = (now: number) => {
      const deltaSec = (now - lastTimestamp) / 1000;
      lastTimestamp = now;

      setViewport((prev) => {
        const windowSpan = prev.end - prev.start;
        const total = totalDuration > 0 ? totalDuration : 10.0;
        let newStart = prev.start + deltaSec * 0.04 * sweepSpeed;
        let newEnd = newStart + windowSpan;

        if (newEnd >= total) {
          newStart = 0;
          newEnd = windowSpan;
        }

        return { start: newStart, end: newEnd };
      });

      animFrameId = requestAnimationFrame(sweepStep);
    };

    animFrameId = requestAnimationFrame(sweepStep);
    return () => cancelAnimationFrame(animFrameId);
  }, [isLiveSweep, sweepSpeed, totalDuration]);

  // 60 FPS Digital Storage Oscilloscope Canvas Renderer
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Dark Phosphor Reticle Grid Background
    ctx.fillStyle = '#030812';
    ctx.fillRect(0, 0, width, height);

    // Grid lines (horizontal & vertical reticle)
    ctx.strokeStyle = 'rgba(0, 240, 255, 0.06)';
    ctx.lineWidth = 1;
    const numHDivs = 8;
    for (let i = 1; i < numHDivs; i++) {
      const y = (height / numHDivs) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    const numVDivs = 10;
    for (let i = 1; i < numVDivs; i++) {
      const x = (width / numVDivs) * i;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Zero-crossing central axis with phosphor tick marks
    const midY = height / 2;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(width, midY);
    ctx.stroke();

    for (let i = 0; i < width; i += 24) {
      ctx.beginPath();
      ctx.moveTo(i, midY - 3);
      ctx.lineTo(i, midY + 3);
      ctx.stroke();
    }

    if (!waveData) {
      ctx.fillStyle = 'rgba(148, 163, 184, 0.5)';
      ctx.font = '12px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(loading ? 'ACQUIRING HIGH-SPEED RF DATA...' : 'STANDBY — AWAITING CAPTURE', width / 2, midY - 6);
      return;
    }

    // Dynamic Auto-Gain Normalization: ensures signal dynamically uses ~75% of oscilloscope display
    let detectedPeak = waveData.peak_amplitude || 0.15;
    if (waveData.max_i && waveData.max_i.length > 0) {
      const sampleMax = Math.max(...waveData.max_i.map((v) => Math.abs(v)));
      if (sampleMax > 0.001) detectedPeak = Math.max(detectedPeak, sampleMax);
    }
    const effectivePeak = autoGain ? Math.max(0.005, detectedPeak) * 1.25 : 0.6;
    const scaleY = ((height / 2) * 0.78 * gainMultiplier) / effectivePeak;

    // 1. Draw In-Phase (I) Component — Electric Cyan Phosphor Glow
    if (showI) {
      ctx.save();
      ctx.shadowColor = '#00f0ff';
      ctx.shadowBlur = 8;
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 2.0;

      if (waveData.mode === 'lod' && waveData.min_i && waveData.max_i) {
        const n = waveData.min_i.length;

        // Subtle gradient fill under curve
        const gradI = ctx.createLinearGradient(0, 0, 0, height);
        gradI.addColorStop(0, 'rgba(0, 240, 255, 0.25)');
        gradI.addColorStop(0.5, 'rgba(0, 240, 255, 0.05)');
        gradI.addColorStop(1, 'rgba(0, 240, 255, 0.25)');
        ctx.fillStyle = gradI;

        ctx.beginPath();
        for (let i = 0; i < n; i++) {
          const x = (i / (n - 1)) * width;
          const yTop = midY - waveData.max_i[i] * scaleY;
          if (i === 0) ctx.moveTo(x, yTop);
          else ctx.lineTo(x, yTop);
        }
        for (let i = n - 1; i >= 0; i--) {
          const x = (i / (n - 1)) * width;
          const yBot = midY - waveData.min_i[i] * scaleY;
          ctx.lineTo(x, yBot);
        }
        ctx.closePath();
        ctx.fill();

        // High-contrast envelope contour
        ctx.beginPath();
        for (let i = 0; i < n; i++) {
          const x = (i / (n - 1)) * width;
          const yMid = midY - ((waveData.max_i[i] + waveData.min_i[i]) / 2) * scaleY;
          if (i === 0) ctx.moveTo(x, yMid);
          else ctx.lineTo(x, yMid);
        }
        ctx.stroke();
      } else if (waveData.mode === 'raw' && waveData.i) {
        ctx.beginPath();
        const n = waveData.i.length;
        for (let i = 0; i < n; i++) {
          const x = (i / (n - 1)) * width;
          const y = midY - waveData.i[i] * scaleY;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      ctx.restore();
    }

    // 2. Draw Quadrature (Q) Component — Neon Violet Glow
    if (showQ) {
      ctx.save();
      ctx.shadowColor = '#c084fc';
      ctx.shadowBlur = 8;
      ctx.strokeStyle = '#c084fc';
      ctx.lineWidth = 2.0;

      if (waveData.mode === 'lod' && waveData.min_q && waveData.max_q) {
        const n = waveData.min_q.length;

        const gradQ = ctx.createLinearGradient(0, 0, 0, height);
        gradQ.addColorStop(0, 'rgba(192, 132, 252, 0.2)');
        gradQ.addColorStop(0.5, 'rgba(192, 132, 252, 0.04)');
        gradQ.addColorStop(1, 'rgba(192, 132, 252, 0.2)');
        ctx.fillStyle = gradQ;

        ctx.beginPath();
        for (let i = 0; i < n; i++) {
          const x = (i / (n - 1)) * width;
          const yTop = midY - waveData.max_q[i] * scaleY;
          if (i === 0) ctx.moveTo(x, yTop);
          else ctx.lineTo(x, yTop);
        }
        for (let i = n - 1; i >= 0; i--) {
          const x = (i / (n - 1)) * width;
          const yBot = midY - waveData.min_q[i] * scaleY;
          ctx.lineTo(x, yBot);
        }
        ctx.closePath();
        ctx.fill();

        ctx.beginPath();
        for (let i = 0; i < n; i++) {
          const x = (i / (n - 1)) * width;
          const yMid = midY - ((waveData.max_q[i] + waveData.min_q[i]) / 2) * scaleY;
          if (i === 0) ctx.moveTo(x, yMid);
          else ctx.lineTo(x, yMid);
        }
        ctx.stroke();
      } else if (waveData.mode === 'raw' && waveData.q) {
        ctx.beginPath();
        const n = waveData.q.length;
        for (let i = 0; i < n; i++) {
          const x = (i / (n - 1)) * width;
          const y = midY - waveData.q[i] * scaleY;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
      ctx.restore();
    }

    // 3. Current Time Cursor Needle
    if (currentTime >= viewport.start && currentTime <= viewport.end) {
      const scrubX = ((currentTime - viewport.start) / (viewport.end - viewport.start)) * width;
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(scrubX, 0);
      ctx.lineTo(scrubX, height);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = '#f59e0b';
      ctx.beginPath();
      ctx.moveTo(scrubX - 5, 0);
      ctx.lineTo(scrubX + 5, 0);
      ctx.lineTo(scrubX, 7);
      ctx.closePath();
      ctx.fill();
    }
  }, [waveData, showI, showQ, viewport, currentTime, loading, autoGain, gainMultiplier]);

  // Minimap Rendering Engine
  useEffect(() => {
    const canvas = minimapRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    ctx.fillStyle = '#060d1a';
    ctx.fillRect(0, 0, width, height);

    // Active Viewport Indicator
    const total = Math.max(0.001, totalDuration);
    const startFrac = Math.max(0, Math.min(1, viewport.start / total));
    const endFrac = Math.max(0, Math.min(1, viewport.end / total));
    const boxX = startFrac * width;
    const boxW = Math.max(8, (endFrac - startFrac) * width);

    ctx.fillStyle = 'rgba(0, 240, 255, 0.25)';
    ctx.fillRect(boxX, 0, boxW, height);
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(boxX, 0, boxW, height);
  }, [viewport, totalDuration]);

  // Mouse Wheel Zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseFrac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const span = viewport.end - viewport.start;
    const mouseTime = viewport.start + mouseFrac * span;

    const factor = e.deltaY < 0 ? 0.7 : 1.4;
    const newSpan = Math.max(0.0001, Math.min(totalDuration || 10.0, span * factor));

    let newStart = mouseTime - mouseFrac * newSpan;
    let newEnd = newStart + newSpan;

    if (newStart < 0) {
      newStart = 0;
      newEnd = Math.min(totalDuration, newSpan);
    }
    if (newEnd > totalDuration && totalDuration > 0) {
      newEnd = totalDuration;
      newStart = Math.max(0, newEnd - newSpan);
    }

    setViewport({ start: newStart, end: newEnd });
  };

  // Mouse Drag / Pan
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    dragStartXRef.current = e.clientX;
    dragStartViewportRef.current = { ...viewport };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const time = viewport.start + frac * (viewport.end - viewport.start);

    setHoverInfo({
      time,
      ampI: waveData?.max_i ? (waveData.max_i[Math.floor(frac * (waveData.max_i.length - 1))] ?? 0) : 0,
      ampQ: waveData?.max_q ? (waveData.max_q[Math.floor(frac * (waveData.max_q.length - 1))] ?? 0) : 0,
    });

    if (isDraggingRef.current) {
      const deltaX = e.clientX - dragStartXRef.current;
      const span = dragStartViewportRef.current.end - dragStartViewportRef.current.start;
      const deltaTime = -(deltaX / rect.width) * span;

      let newStart = dragStartViewportRef.current.start + deltaTime;
      let newEnd = dragStartViewportRef.current.end + deltaTime;

      if (newStart < 0) {
        newEnd -= newStart;
        newStart = 0;
      }
      if (newEnd > totalDuration && totalDuration > 0) {
        newStart -= (newEnd - totalDuration);
        newEnd = totalDuration;
      }

      setViewport({ start: Math.max(0, newStart), end: Math.max(0.0002, newEnd) });
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleClick = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const time = viewport.start + frac * (viewport.end - viewport.start);
    onTimeChange(time);
  };

  const handleResetZoom = () => {
    setViewport({
      start: 0,
      end: Math.min(0.05, totalDuration || 0.05),
    });
  };

  const setPresetSpan = (seconds: number) => {
    const span = Math.min(seconds, totalDuration || seconds);
    const newStart = viewport.start;
    setViewport({
      start: newStart,
      end: newStart + span,
    });
  };

  const formatTime = (sec: number) => {
    if (sec < 0.001) return `${(sec * 1e6).toFixed(1)} µs`;
    if (sec < 1.0) return `${(sec * 1000).toFixed(2)} ms`;
    return `${sec.toFixed(3)} s`;
  };

  const peakMv = waveData?.peak_amplitude ? (waveData.peak_amplitude * 1000).toFixed(1) : '150.0';
  const rmsMv = waveData?.rms_power ? (waveData.rms_power * 1000).toFixed(1) : '95.2';

  return (
    <div className="signallab-panel p-4 flex flex-col gap-3 relative select-none">
      {/* Header & Controls Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#00f0ff] animate-pulse" />
            <span className="font-sans text-xs font-semibold text-white tracking-wide">
              REAL-TIME TIME-DOMAIN OSCILLOSCOPE
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 font-mono text-[10px] text-slate-400 bg-white/[0.04] px-2.5 py-1 rounded border border-white/[0.08]">
            <span>Peak: <strong className="text-[#00f0ff]">{peakMv} mV</strong></span>
            <span className="text-slate-600">|</span>
            <span>RMS: <strong className="text-emerald-400">{rmsMv} mV</strong></span>
            <span className="text-slate-600">|</span>
            <span>Rate: <strong className="text-slate-200">{(sampleRate / 1e3).toFixed(1)} kSps</strong></span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Live Sweep Play/Pause Toggle */}
          <button
            onClick={() => setIsLiveSweep(!isLiveSweep)}
            className={`signallab-btn text-[11px] ${isLiveSweep ? 'active text-[#00f0ff]' : 'text-slate-400'}`}
          >
            {isLiveSweep ? <Pause className="w-3 h-3 text-[#00f0ff]" /> : <Play className="w-3 h-3 text-emerald-400" />}
            <span>{isLiveSweep ? 'PAUSE SWEEP' : 'LIVE SWEEP'}</span>
          </button>

          {/* Auto-Gain Toggle */}
          <button
            onClick={() => setAutoGain(!autoGain)}
            className={`signallab-btn text-[10px] ${autoGain ? 'active text-emerald-400' : 'text-slate-400'}`}
          >
            <span>AUTO GAIN</span>
          </button>

          {/* Gain Multiplier */}
          <div className="flex items-center bg-white/[0.04] border border-white/[0.08] rounded p-0.5 text-[10px] font-mono">
            {[1, 2, 5, 10].map((m) => (
              <button
                key={m}
                onClick={() => { setGainMultiplier(m); setAutoGain(false); }}
                className={`px-1.5 py-0.5 rounded ${gainMultiplier === m && !autoGain ? 'bg-[#00f0ff] text-black font-bold' : 'text-slate-400 hover:text-white'}`}
              >
                {m}x
              </button>
            ))}
          </div>

          {/* Channel I & Q Toggles */}
          <button
            onClick={() => setShowI(!showI)}
            className={`signallab-btn text-[10px] ${showI ? 'active text-[#00f0ff]' : 'text-slate-500'}`}
          >
            <span className="w-2 h-2 rounded-full bg-[#00f0ff]" />
            I-TRACE
          </button>

          <button
            onClick={() => setShowQ(!showQ)}
            className={`signallab-btn text-[10px] ${showQ ? 'active text-[#c084fc]' : 'text-slate-500'}`}
          >
            <span className="w-2 h-2 rounded-full bg-[#c084fc]" />
            Q-TRACE
          </button>

          {/* Reset Zoom */}
          <button
            onClick={handleResetZoom}
            title="Reset Scope View"
            className="signallab-btn p-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-300" />
          </button>
        </div>
      </div>

      {/* Main High-Performance Oscilloscope Canvas */}
      <div
        className="relative w-full h-52 bg-[#030812] rounded-lg border border-[rgba(0,240,255,0.18)] overflow-hidden cursor-crosshair shadow-inner"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
      >
        <canvas
          ref={canvasRef}
          width={1200}
          height={210}
          className="w-full h-full block"
        />

        {/* Telemetry Tooltip Badge */}
        {hoverInfo && (
          <div className="absolute top-2 right-2 bg-slate-900/95 border border-cyan-500/40 rounded px-3 py-1.5 text-[10px] font-mono text-slate-200 pointer-events-none flex items-center gap-3 backdrop-blur-md shadow-lg">
            <span>t = <strong className="text-white">{formatTime(hoverInfo.time)}</strong></span>
            <span>I = <strong className="text-[#00f0ff]">{hoverInfo.ampI.toFixed(3)}</strong></span>
            <span>Q = <strong className="text-[#c084fc]">{hoverInfo.ampQ.toFixed(3)}</strong></span>
          </div>
        )}

        {/* Bottom Window Readout */}
        <div className="absolute bottom-2 left-2 pointer-events-none font-mono text-[10px] text-cyan-400/80 bg-black/60 px-2 py-0.5 rounded backdrop-blur">
          Window: [{formatTime(viewport.start)} → {formatTime(viewport.end)}] (Δ {formatTime(viewport.end - viewport.start)})
        </div>
      </div>

      {/* Quick Timebase Presets & Minimap Navigation */}
      <div className="flex flex-col gap-1.5 pt-1">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-500">TIMEBASE:</span>
            {[0.001, 0.005, 0.02, 0.1, 0.5].map((sec) => (
              <button
                key={sec}
                onClick={() => setPresetSpan(sec)}
                className="px-2 py-0.5 rounded bg-white/[0.04] hover:bg-white/[0.1] border border-white/[0.08] text-slate-300 hover:text-white transition"
              >
                {formatTime(sec)}
              </button>
            ))}
          </div>
          <span className="text-slate-500">Buffer: 0.00 s → {totalDuration.toFixed(2)} s</span>
        </div>

        {/* Minimap Timeline Scrub Bar */}
        <div className="w-full h-4 bg-slate-950 rounded border border-slate-800/80 overflow-hidden cursor-pointer">
          <canvas
            ref={minimapRef}
            width={800}
            height={16}
            className="w-full h-full block"
          />
        </div>
      </div>
    </div>
  );
};
