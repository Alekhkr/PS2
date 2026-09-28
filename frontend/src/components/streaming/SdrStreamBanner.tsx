import React, { useState, useEffect, useRef } from 'react';
import { Radio, Activity, Play, Pause } from 'lucide-react';

interface SdrTelemetry {
  timestamp: number;
  mode: string;
  mod_type: string;
  sample_rate: number;
  center_freq_hz: number;
  snr_db: number;
  rms_dbfs: number;
  papr_db: number;
  i_samples: number[];
  q_samples: number[];
  fft_power: number[];
}

export const SdrStreamBanner: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [source, setSource] = useState<'synthetic' | 'replay' | 'hardware'>('synthetic');
  const [modType, setModType] = useState('16QAM');
  const [telemetry, setTelemetry] = useState<SdrTelemetry | null>(null);
  const [fps, setFps] = useState<number>(0);
  const [status, setStatus] = useState<'disconnected' | 'connecting' | 'streaming'>('disconnected');

  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(performance.now());

  useEffect(() => {
    if (!isActive) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setStatus('disconnected');
      return;
    }

    setStatus('connecting');
    // Compute WebSocket URL
    const isDev = window.location.port === '5173';
    const wsUrl = isDev
      ? 'ws://127.0.0.1:8000/ws/sdr'
      : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/sdr`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('streaming');
      ws.send(JSON.stringify({ action: 'set_source', source, mod: modType }));
    };

    ws.onmessage = (event) => {
      try {
        const data: SdrTelemetry = JSON.parse(event.data);
        setTelemetry(data);

        // Frame rate calculation
        frameCountRef.current += 1;
        const now = performance.now();
        if (now - lastFpsTimeRef.current >= 1000) {
          setFps(Math.round((frameCountRef.current * 1000) / (now - lastFpsTimeRef.current)));
          frameCountRef.current = 0;
          lastFpsTimeRef.current = now;
        }

        // Render mini FFT spectrum on canvas
        if (canvasRef.current && data.fft_power) {
          const canvas = canvasRef.current;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            const w = canvas.width;
            const h = canvas.height;
            ctx.fillStyle = '#020610';
            ctx.fillRect(0, 0, w, h);

            // Grid lines
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.08)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(0, h * 0.5);
            ctx.lineTo(w, h * 0.5);
            ctx.moveTo(w * 0.5, 0);
            ctx.lineTo(w * 0.5, h);
            ctx.stroke();

            // FFT power trace
            const powers = data.fft_power;
            const step = w / (powers.length - 1);
            ctx.strokeStyle = '#00f0ff';
            ctx.lineWidth = 1.8;
            ctx.shadowColor = '#00f0ff';
            ctx.shadowBlur = 6;
            ctx.beginPath();

            for (let i = 0; i < powers.length; i++) {
              // Map dB from [-80, 0] to [h, 0]
              const db = Math.max(-80, Math.min(0, powers[i]));
              const y = h - ((db + 80) / 80) * h;
              const x = i * step;
              if (i === 0) ctx.moveTo(x, y);
              else ctx.lineTo(x, y);
            }
            ctx.stroke();
            ctx.shadowBlur = 0;
          }
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    ws.onerror = () => {
      setStatus('disconnected');
    };

    ws.onclose = () => {
      setStatus('disconnected');
    };

    return () => {
      ws.close();
    };
  }, [isActive]);

  const sendConfig = (newSource: string, newMod: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: 'set_source',
          source: newSource,
          mod: newMod,
        })
      );
    }
  };

  const handleSourceChange = (src: 'synthetic' | 'replay' | 'hardware') => {
    setSource(src);
    sendConfig(src, modType);
  };

  const handleModChange = (mod: string) => {
    setModType(mod);
    sendConfig(source, mod);
  };

  return (
    <div className="signallab-panel p-4 flex flex-col gap-3 border border-white/[0.08] bg-black/60 backdrop-blur-md">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Radio className={`w-4 h-4 ${isActive ? 'text-[#00f0ff] animate-pulse' : 'text-slate-500'}`} />
            {isActive && (
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#00f0ff] animate-ping" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-white tracking-wider uppercase">
                LIVE SDR HARDWARE STREAMING & SYNTHESIZER
              </span>
              <span
                className={`font-mono text-[9px] px-2 py-0.5 rounded border uppercase font-semibold ${
                  status === 'streaming'
                    ? 'text-emerald-400 bg-emerald-950/60 border-emerald-800/40'
                    : status === 'connecting'
                    ? 'text-yellow-400 bg-yellow-950/60 border-yellow-800/40'
                    : 'text-slate-500 bg-slate-900 border-white/10'
                }`}
              >
                {status === 'streaming' ? `LIVE (${fps} FPS)` : status}
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              Real-time complex I/Q WebSocket transport (30 Hz) · Hardware RTL-SDR / Capture Replay / Continuous Channel Synthesizer
            </span>
          </div>
        </div>

        {/* Toggle Live Streaming Button */}
        <button
          onClick={() => setIsActive((prev) => !prev)}
          className={`signallab-btn text-xs px-3.5 py-1.5 font-bold transition flex items-center gap-2 ${
            isActive
              ? 'text-rose-400 bg-rose-950/40 border-rose-500/40 hover:bg-rose-900/60'
              : 'text-[#00f0ff] bg-cyan-950/40 border-cyan-500/40 hover:bg-cyan-900/60'
          }`}
        >
          {isActive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          <span>{isActive ? 'HALT SDR STREAM' : 'ENGAGE LIVE SDR'}</span>
        </button>
      </div>

      {/* Expanded Controls when Active */}
      {isActive && (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 pt-3 border-t border-white/[0.08] font-mono text-xs">
          {/* Controls: Source & Mod (5 cols) */}
          <div className="md:col-span-5 flex flex-col gap-3">
            <div className="flex flex-col gap-1.5">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">IQ STREAM SOURCE:</span>
              <div className="grid grid-cols-3 gap-1.5">
                {[
                  { id: 'synthetic', label: 'SYNTHETIC' },
                  { id: 'replay', label: 'REPLAY' },
                  { id: 'hardware', label: 'RTL-SDR' },
                ].map((s) => (
                  <button
                    key={s.id}
                    onClick={() => handleSourceChange(s.id as any)}
                    className={`py-1.5 px-2 rounded border text-[10px] font-bold text-center transition ${
                      source === s.id
                        ? 'bg-cyan-950/60 border-cyan-400 text-white shadow-sm'
                        : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-white'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {source === 'synthetic' && (
              <div className="flex flex-col gap-1.5">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider">SYNTHETIC MODULATION:</span>
                <div className="grid grid-cols-4 gap-1">
                  {['16QAM', 'QPSK', 'FSK', 'CHIRP'].map((m) => (
                    <button
                      key={m}
                      onClick={() => handleModChange(m)}
                      className={`py-1 px-1.5 rounded border text-[10px] font-bold text-center transition ${
                        modType === m
                          ? 'bg-cyan-950/60 border-cyan-400 text-white shadow-sm'
                          : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-white'
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Live Metrics Telemetry Badges */}
            <div className="grid grid-cols-3 gap-2 pt-1 text-[10px]">
              <div className="bg-white/[0.03] p-1.5 rounded border border-white/[0.06]">
                <span className="text-slate-400 block text-[9px]">RMS POWER:</span>
                <span className="text-[#00f0ff] font-bold">{telemetry ? `${telemetry.rms_dbfs} dBFS` : '--'}</span>
              </div>
              <div className="bg-white/[0.03] p-1.5 rounded border border-white/[0.06]">
                <span className="text-slate-400 block text-[9px]">PAPR:</span>
                <span className="text-purple-400 font-bold">{telemetry ? `${telemetry.papr_db} dB` : '--'}</span>
              </div>
              <div className="bg-white/[0.03] p-1.5 rounded border border-white/[0.06]">
                <span className="text-slate-400 block text-[9px]">SAMPLE RATE:</span>
                <span className="text-emerald-400 font-bold">{telemetry ? `${telemetry.sample_rate / 1e3} kSps` : '--'}</span>
              </div>
            </div>
          </div>

          {/* Mini Live FFT Power Canvas (7 cols) */}
          <div className="md:col-span-7 flex flex-col gap-1.5">
            <div className="flex justify-between items-center text-[10px]">
              <span className="text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Activity className="w-3 h-3 text-[#00f0ff]" />
                LIVE FFT REAL-TIME SPECTRUM (-80 dB to 0 dB):
              </span>
              <span className="text-slate-500 font-mono text-[9px]">128 FREQUENCY BINS</span>
            </div>
            <div className="relative w-full h-24 rounded border border-cyan-500/30 overflow-hidden bg-[#020610]">
              <canvas
                ref={canvasRef}
                width={360}
                height={96}
                className="w-full h-full block"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
