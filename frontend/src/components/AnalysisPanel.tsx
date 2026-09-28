import React from 'react';
import type { AnalysisResponse } from '../types';
import { Cpu, CheckCircle2 } from 'lucide-react';

interface AnalysisPanelProps {
  analysis: AnalysisResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  analysis,
  loading,
  onRefresh,
}) => {
  const topMod = analysis?.modulation?.name || 'ANALYZING...';
  const score = analysis?.modulation?.score ? Math.round(analysis.modulation.score * 100) : 0;
  const candidates = analysis?.modulation?.candidates || [];

  return (
    <div className="austensor-panel p-4 flex flex-col gap-3.5 select-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-emerald-400" />
          <span className="font-mono text-xs font-bold text-white tracking-wide">
            HYBRID AMC NEURAL & DSP
          </span>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="austensor-btn text-[10px] py-1 px-2.5 text-emerald-400 hover:text-white"
        >
          {loading ? 'COMPUTING...' : 'RE-RUN AUDIT'}
        </button>
      </div>

      {/* Top Hypothesis Banner */}
      <div className="bg-gradient-to-r from-emerald-950/40 via-cyan-950/20 to-transparent p-3 rounded-lg border border-emerald-800/40">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span className="font-['Syne'] text-base font-bold text-white uppercase tracking-wider">
              {topMod}
            </span>
          </div>
          <span className="font-mono text-xs font-bold text-emerald-400">{score}% CONFIDENCE</span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden mb-2">
          <div
            className="h-full bg-gradient-to-r from-cyan-400 to-emerald-400 transition-all duration-500 rounded-full"
            style={{ width: `${score}%` }}
          />
        </div>

        {/* Evidence Pill tags */}
        <div className="flex flex-wrap gap-1.5">
          {analysis?.modulation?.evidence?.map((ev, i) => (
            <span
              key={i}
              className="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-900/80 text-slate-300 border border-slate-800"
            >
              {ev}
            </span>
          )) || (
            <span className="text-[9px] font-mono text-slate-500">Estimating feature moments...</span>
          )}
        </div>
      </div>

      {/* Numerical Metrics Matrix */}
      <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
        <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800/80">
          <div className="text-slate-400 text-[10px] uppercase">Occupied BW (99%)</div>
          <div className="text-white font-bold text-sm mt-0.5">
            {analysis ? `${(analysis.occupied_bw_hz / 1e3).toFixed(1)} kHz` : '--'}
          </div>
        </div>

        <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800/80">
          <div className="text-slate-400 text-[10px] uppercase">Symbol Rate</div>
          <div className="text-white font-bold text-sm mt-0.5">
            {analysis && analysis.symbol_rate_baud > 0
              ? `${(analysis.symbol_rate_baud / 1e3).toFixed(2)} kBaud`
              : 'CW / Unmodulated'}
          </div>
        </div>

        <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800/80">
          <div className="text-slate-400 text-[10px] uppercase">Carrier Offset (CFO)</div>
          <div className="text-[#00f0ff] font-bold text-sm mt-0.5">
            {analysis ? `${analysis.carrier_offset_hz > 0 ? '+' : ''}${analysis.carrier_offset_hz.toFixed(1)} Hz` : '--'}
          </div>
        </div>

        <div className="bg-slate-900/50 p-2.5 rounded border border-slate-800/80">
          <div className="text-slate-400 text-[10px] uppercase">Signal Bursts</div>
          <div className="text-amber-400 font-bold text-sm mt-0.5">
            {analysis ? `${analysis.burst_count} detected` : '--'}
          </div>
        </div>
      </div>

      {/* Alternative Ranked Candidates */}
      {candidates.length > 1 && (
        <div className="flex flex-col gap-1.5 pt-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
            Alternative Hypotheses
          </span>
          <div className="flex flex-col gap-1">
            {candidates.slice(1, 4).map((c, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between bg-slate-900/30 px-2 py-1 rounded text-[10px] font-mono"
              >
                <span className="text-slate-300">{c.name}</span>
                <span className="text-slate-500">{(c.score * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
