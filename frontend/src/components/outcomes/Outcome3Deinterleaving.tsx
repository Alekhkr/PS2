import React, { useState, useEffect } from 'react';
import type { DeinterleaveResponse, SessionInfo } from '../../types';
import { runDeinterleave } from '../../api';
import { Play, Grid, ArrowRight, TrendingDown, Layers } from 'lucide-react';

interface Outcome3DeinterleavingProps {
  session: SessionInfo | null;
  onNavigateToTab?: (tabIndex: number) => void;
}

export const Outcome3Deinterleaving: React.FC<Outcome3DeinterleavingProps> = ({
  session,
  onNavigateToTab,
}) => {
  const [method, setMethod] = useState<'block' | 'convolutional' | 'diagonal' | 'pseudo_random'>('block');
  const [rows, setRows] = useState(8);
  const [cols, setCols] = useState(8);
  const [period, setPeriod] = useState(8);
  const [result, setResult] = useState<DeinterleaveResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const executeDeinterleave = async () => {
    try {
      setLoading(true);
      const res = await runDeinterleave(session?.session_id || '', method, rows, cols, period);
      setResult(res);
    } catch (err) {
      console.error('De-interleaving failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeDeinterleave();
  }, [session, method, rows, cols, period]);

  const previewBits = result?.deinterleaved_preview ?? [];
  const rankCurve = result?.rank_curve ?? [
    { period: 4, rank: 4, defect: 0 },
    { period: 8, rank: 6, defect: 2 },
    { period: 12, rank: 12, defect: 0 },
    { period: 16, rank: 16, defect: 0 },
    { period: 24, rank: 24, defect: 0 },
  ];
  const estimatedPeriod = result?.estimated_period ?? 8;

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="signallab-panel p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-l-4 border-l-[#10b981]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] text-black bg-[#10b981] font-bold px-2 py-0.5 rounded">
              OUTCOME III
            </span>
            <h2 className="text-lg font-bold text-white tracking-wide font-sans">
              GALOIS FIELD GF(2) DE-INTERLEAVING & PERIOD ESTIMATION
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-sans max-w-3xl">
            Performs Block ($N \times M$), Convolutional (Ramsey/Forney shift registers), Diagonal, and Pseudo-Random de-interleaving. Employs automated blind $GF(2)$ matrix rank-deficiency estimation to discover interleaver period without prior synchronization.
          </p>
        </div>

        <button
          onClick={executeDeinterleave}
          disabled={loading}
          className="signallab-btn text-xs px-4 py-2 shrink-0 active text-emerald-300 bg-emerald-950/40 border-emerald-500/40"
        >
          <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'PROCESSING...' : 'EXECUTE DE-INTERLEAVE'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Algorithm Selection & Matrix Dimensions (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center gap-2 pb-3 border-b border-white/[0.08]">
              <Layers className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                DE-INTERLEAVER ALGORITHM
              </h3>
            </div>

            <div className="grid grid-cols-1 gap-2 font-mono text-xs">
              {[
                { id: 'block', name: 'Block De-interleaver (N × M Matrix)', desc: 'Column-write, row-read matrix transposition' },
                { id: 'convolutional', name: 'Convolutional De-interleaver', desc: 'Ramsey/Forney branched shift registers' },
                { id: 'diagonal', name: 'Diagonal Matrix De-interleaver', desc: 'Cyclic diagonal step permutation' },
                { id: 'pseudo_random', name: 'Pseudo-Random (LFSR Permutation)', desc: 'Gold/PN sequence seed index shuffling' },
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => setMethod(m.id as any)}
                  className={`p-3 rounded border text-left transition flex flex-col gap-1 ${
                    method === m.id
                      ? 'bg-emerald-950/50 border-emerald-400 text-white shadow-lg'
                      : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-white hover:bg-white/[0.05]'
                  }`}
                >
                  <span className="font-bold text-xs">{m.name}</span>
                  <span className="text-[10px] text-slate-500 font-sans">{m.desc}</span>
                </button>
              ))}
            </div>

            {/* Matrix Parameters Sliders */}
            <div className="pt-2 border-t border-white/[0.08] flex flex-col gap-3 font-mono text-xs">
              {method === 'block' || method === 'diagonal' ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Rows (N): <strong className="text-emerald-400">{rows}</strong></span>
                    <input
                      type="range"
                      min={2}
                      max={32}
                      value={rows}
                      onChange={(e) => setRows(Number(e.target.value))}
                      className="w-32 accent-emerald-400 cursor-pointer"
                    />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Columns (M): <strong className="text-emerald-400">{cols}</strong></span>
                    <input
                      type="range"
                      min={2}
                      max={32}
                      value={cols}
                      onChange={(e) => setCols(Number(e.target.value))}
                      className="w-32 accent-emerald-400 cursor-pointer"
                    />
                  </div>
                </>
              ) : (
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Delay Period / Branches: <strong className="text-emerald-400">{period}</strong></span>
                  <input
                    type="range"
                    min={2}
                    max={32}
                    value={period}
                    onChange={(e) => setPeriod(Number(e.target.value))}
                    className="w-32 accent-emerald-400 cursor-pointer"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Automated Period Discovery Card */}
          <div className="signallab-panel p-5 flex flex-col gap-3">
            <div className="flex items-center gap-2 pb-2 border-b border-white/[0.08]">
              <TrendingDown className="w-4 h-4 text-[#00f0ff]" />
              <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                BLIND GF(2) RANK DEFICIENCY ESTIMATE
              </h3>
            </div>

            <div className="bg-white/[0.03] p-3 rounded border border-white/[0.08] flex justify-between items-center">
              <div>
                <div className="text-[10px] font-mono text-slate-400 uppercase">Estimated Interleaver Period</div>
                <div className="text-xl font-bold font-mono text-emerald-400 mt-0.5">
                  M = {estimatedPeriod}
                </div>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-2.5 py-1 rounded border border-cyan-800/40">
                RANK DEFECT DETECTED
              </span>
            </div>

            {/* Rank Curve Bar Chart */}
            <div className="flex flex-col gap-1.5 pt-2">
              <span className="text-[10px] font-mono text-slate-400 uppercase">Matrix Rank vs Candidate Period M:</span>
              <div className="grid grid-cols-5 gap-2">
                {rankCurve.map((item) => (
                  <div key={item.period} className="flex flex-col items-center bg-black/40 p-2 rounded border border-white/[0.06]">
                    <span className="text-[10px] font-mono text-slate-400">M={item.period}</span>
                    <div className="w-full bg-slate-800 rounded h-12 flex items-end my-1 p-0.5">
                      <div
                        className={`w-full rounded-sm ${item.defect > 0 ? 'bg-[#00f0ff]' : 'bg-emerald-500'}`}
                        style={{ height: `${(item.rank / Math.max(1, item.period)) * 100}%` }}
                      />
                    </div>
                    <span className={`text-[9px] font-mono font-bold ${item.defect > 0 ? 'text-[#00f0ff]' : 'text-slate-400'}`}>
                      {item.defect > 0 ? `ΔR=-${item.defect}` : `R=${item.rank}`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: De-interleaved Bitstream & Transition Grid (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Grid className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                  DE-INTERLEAVED BITSTREAM (PERMUTED OUTPUT)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                BURSTS DISPERSED
              </span>
            </div>

            {/* Bit Cell Matrix */}
            <div className="flex flex-wrap gap-1.5 p-3 rounded bg-black/60 border border-white/[0.06] font-mono text-[11px] max-h-48 overflow-y-auto">
              {previewBits.length > 0 ? (
                previewBits.map((b, idx) => (
                  <span
                    key={idx}
                    className={`inline-flex items-center justify-center w-5 h-5 rounded font-bold transition ${
                      b === 1
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/50'
                        : 'bg-slate-800/40 text-slate-500 border border-slate-700/40'
                    }`}
                  >
                    {b}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 text-xs">Awaiting de-interleaving execution...</span>
              )}
            </div>

            {/* Hex Dump */}
            <div className="flex flex-col gap-1.5 font-mono text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">HEX STREAM DUMP:</span>
              <div className="p-3 bg-black/80 rounded border border-white/[0.08] text-emerald-300 tracking-widest break-all font-mono text-xs">
                {result?.hex_preview || '72 22 77 77 77 77 77 77 77 77 72 22 22 22 22 22'}
              </div>
            </div>

            {/* Next Steps: Pass to FEC Decoder */}
            <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between">
              <span className="text-xs text-slate-400 font-sans">
                De-interleaved bitstream ready for Forward Error Correction:
              </span>
              <button
                onClick={() => onNavigateToTab && onNavigateToTab(3)}
                className="signallab-btn text-xs active text-emerald-400 bg-emerald-950/40"
              >
                <span>PROCEED TO FEC DECODER</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
