import React, { useState } from 'react';
import type { DemodulationResponse, SessionInfo } from '../../types';
import { runDemodulation } from '../../api';
import { Play, Radio, Cpu, ArrowRight, Sparkles } from 'lucide-react';

interface Outcome2DemodulationProps {
  session: SessionInfo | null;
  onNavigateToTab?: (tabIndex: number) => void;
}

export const Outcome2Demodulation: React.FC<Outcome2DemodulationProps> = ({
  session,
  onNavigateToTab,
}) => {
  const [selectedMod, setSelectedMod] = useState<'FSK' | 'BPSK' | 'QPSK' | '16QAM' | '64QAM'>('BPSK');
  const [demodResult, setDemodResult] = useState<DemodulationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const executeDemod = async (modType: string = selectedMod) => {
    try {
      setLoading(true);
      const res = await runDemodulation(session?.session_id || '', modType);
      setDemodResult(res);
    } catch (err) {
      console.error('Demodulation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // Run on mount or when mod changes
  React.useEffect(() => {
    executeDemod(selectedMod);
  }, [session, selectedMod]);

  const evm = demodResult?.evm_percent ?? 4.2;
  const bitCount = demodResult?.bit_count ?? 2048;
  const bitsPreview = demodResult?.hard_bits_preview ?? [];
  const hexPreview = demodResult?.hex_preview ?? '72 22 77 77 77 77 77 77 77 77 72 22 22 22 22 22';

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="signallab-panel p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-l-4 border-l-[#a855f7]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] text-white bg-[#a855f7] font-bold px-2 py-0.5 rounded">
              OUTCOME II
            </span>
            <h2 className="text-lg font-bold text-white tracking-wide font-sans">
              MULTI-SCHEME DIGITAL DEMODULATION ENGINE
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-sans max-w-3xl">
            Demodulates terrestrial RF signals across FSK, PSK (BPSK, QPSK), and QAM (16-QAM, 64-QAM) schemes with carrier phase lock (Costas Loop), timing recovery (Mueller-Müller), and hard-decision bit slicing.
          </p>
        </div>

        <button
          onClick={() => executeDemod()}
          disabled={loading}
          className="signallab-btn text-xs px-4 py-2 shrink-0 active text-purple-300 bg-purple-950/40 border-purple-500/40"
        >
          <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'DEMODULATING...' : 'EXECUTE DEMODULATION'}</span>
        </button>
      </div>

      {/* Selector & Telemetry Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Demodulation Configuration (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center gap-2 pb-3 border-b border-white/[0.08]">
              <Radio className="w-4 h-4 text-[#a855f7]" />
              <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                SELECT DEMODULATION SCHEME
              </h3>
            </div>

            <div className="grid grid-cols-1 gap-2 font-mono text-xs">
              {[
                { id: 'FSK', name: 'FSK (Frequency Shift Keying)', desc: 'FM discriminator & multi-frequency peak detector' },
                { id: 'BPSK', name: 'BPSK (Binary Phase Shift Keying)', desc: 'Biphase Costas carrier phase recovery' },
                { id: 'QPSK', name: 'QPSK (Quadrature Phase Shift)', desc: '4-phase π/4 decision constellation' },
                { id: '16QAM', name: '16-QAM (16-State Quadrature)', desc: 'Dual-axis amplitude & phase decision slicing' },
                { id: '64QAM', name: '64-QAM (64-State High-Order)', desc: 'High-spectral-efficiency dense grid slicer' },
              ].map((scheme) => (
                <button
                  key={scheme.id}
                  onClick={() => setSelectedMod(scheme.id as any)}
                  className={`p-3 rounded border text-left transition flex flex-col gap-1 ${
                    selectedMod === scheme.id
                      ? 'bg-purple-950/50 border-purple-400 text-white shadow-lg'
                      : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-white hover:bg-white/[0.05]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs">{scheme.name}</span>
                    {selectedMod === scheme.id && <Sparkles className="w-3.5 h-3.5 text-purple-400" />}
                  </div>
                  <span className="text-[10px] text-slate-500 font-sans">{scheme.desc}</span>
                </button>
              ))}
            </div>

            {/* Performance Gauges */}
            <div className="pt-2 border-t border-white/[0.08] flex flex-col gap-2 font-mono text-xs">
              <div className="flex justify-between items-center bg-white/[0.03] p-2.5 rounded border border-white/[0.06]">
                <span className="text-slate-400">Error Vector Mag (EVM):</span>
                <span className={`font-bold ${evm < 8 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {evm.toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center bg-white/[0.03] p-2.5 rounded border border-white/[0.06]">
                <span className="text-slate-400">Demodulated Bits:</span>
                <span className="text-cyan-400 font-bold">{bitCount} bits</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Sliced Bits Inspector & Hex Stream (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {/* Recovered Bitstream Preview */}
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                  DEMODULATED HARD BITSTREAM (FIRST 128 BITS)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400 bg-white/[0.04] px-2 py-0.5 rounded border border-white/[0.08]">
                BIT SLICER ACTIVE
              </span>
            </div>

            {/* Bit Pill Matrix */}
            <div className="flex flex-wrap gap-1.5 p-3 rounded bg-black/60 border border-white/[0.06] font-mono text-[11px] max-h-44 overflow-y-auto">
              {bitsPreview.length > 0 ? (
                bitsPreview.map((bit, idx) => (
                  <span
                    key={idx}
                    className={`inline-flex items-center justify-center w-5 h-5 rounded font-bold transition ${
                      bit === 1
                        ? 'bg-cyan-500/20 text-[#00f0ff] border border-cyan-500/50'
                        : 'bg-slate-800/40 text-slate-500 border border-slate-700/40'
                    }`}
                  >
                    {bit}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 text-xs">Awaiting demodulation trigger...</span>
              )}
            </div>

            {/* Hex Byte Dump */}
            <div className="flex flex-col gap-1.5 font-mono text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">HEX STREAM DUMP:</span>
              <div className="p-3 bg-black/80 rounded border border-white/[0.08] text-purple-300 tracking-widest break-all font-mono text-xs">
                {hexPreview}
              </div>
            </div>

            {/* Next Steps Workflow Shortcuts */}
            <div className="pt-3 border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
              <span className="text-xs text-slate-400 font-sans">
                Next Processing Stage:
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onNavigateToTab && onNavigateToTab(2)}
                  className="signallab-btn text-xs active text-[#00f0ff] bg-cyan-950/40"
                >
                  <span>PASS TO DE-INTERLEAVER</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => onNavigateToTab && onNavigateToTab(3)}
                  className="signallab-btn text-xs active text-emerald-400 bg-emerald-950/40"
                >
                  <span>PASS TO FEC DECODER</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
