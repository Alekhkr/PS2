import React, { useState, useEffect } from 'react';
import type { DemodulationResponse } from '../types';
import { runDemodulation } from '../api';
import { Binary, ShieldCheck, Search, Key } from 'lucide-react';

interface BitstreamInspectorProps {
  sessionId: string | null;
  detectedMod?: string;
}

export const BitstreamInspector: React.FC<BitstreamInspectorProps> = ({
  sessionId,
  detectedMod = 'BPSK',
}) => {
  const [modType, setModType] = useState<string>('BPSK');
  const [demodData, setDemodData] = useState<DemodulationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (detectedMod) {
      if (detectedMod.includes('QPSK')) setModType('QPSK');
      else if (detectedMod.includes('16QAM')) setModType('16QAM');
      else if (detectedMod.includes('64QAM')) setModType('64QAM');
      else setModType('BPSK');
    }
  }, [detectedMod]);

  const handleDemodulate = async () => {
    if (!sessionId) return;
    try {
      setLoading(true);
      const res = await runDemodulation(sessionId, modType);
      setDemodData(res);
    } catch (err) {
      console.error('Demodulation error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Run on mount or session change
  useEffect(() => {
    if (sessionId) {
      handleDemodulate();
    }
  }, [sessionId, modType]);

  return (
    <div className="austensor-panel p-4 flex flex-col gap-3 select-none">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Binary className="w-4 h-4 text-cyan-400" />
          <span className="font-mono text-xs font-bold text-white tracking-wide">
            BITSTREAM & PROTOCOL SYNC
          </span>
        </div>

        {/* Mod Type Select */}
        <div className="flex items-center gap-2">
          <select
            value={modType}
            onChange={(e) => setModType(e.target.value)}
            className="bg-slate-900 text-[10px] font-mono text-slate-200 border border-slate-700 rounded px-2 py-1 outline-none"
          >
            <option value="BPSK">BPSK</option>
            <option value="QPSK">QPSK</option>
            <option value="16QAM">16QAM</option>
            <option value="64QAM">64QAM</option>
          </select>

          <button
            onClick={handleDemodulate}
            disabled={loading}
            className="austensor-btn text-[10px] py-1 px-2.5 text-cyan-400"
          >
            {loading ? 'DEMODULATING...' : 'SLICING BITS'}
          </button>
        </div>
      </div>

      {/* Sync Word Correlation Matches */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
          <Search className="w-3 h-3 text-amber-400" /> SYNC DETECTIONS:
        </span>
        {demodData?.sync_matches && demodData.sync_matches.length > 0 ? (
          demodData.sync_matches.map((m, i) => (
            <span
              key={i}
              className="text-[10px] font-mono bg-amber-950/40 border border-amber-600/50 text-amber-300 px-2 py-0.5 rounded flex items-center gap-1"
            >
              <Key className="w-2.5 h-2.5" /> {m.pattern} @ bit {m.bit_index} ({(m.score * 100).toFixed(0)}%)
            </span>
          ))
        ) : (
          <span className="text-[10px] font-mono text-slate-500 italic">No preamble detected in window</span>
        )}
      </div>

      {/* Hex Dump Display */}
      <div className="bg-black/80 rounded border border-slate-800 p-2.5 font-mono text-[10px] text-slate-300 overflow-x-auto scanlines">
        {demodData?.hex_preview ? (
          <div className="space-y-1">
            <div className="text-slate-500 text-[9px] border-b border-slate-800 pb-1 flex justify-between">
              <span>HEX DUMP (OFFSET 0x0000 - 0x0080)</span>
              <span>BITS: {demodData.bit_count} | EVM: {demodData.evm_percent.toFixed(2)}%</span>
            </div>
            <div className="font-mono text-cyan-300 leading-relaxed tracking-wider break-all pt-1">
              {demodData.hex_preview}
            </div>
          </div>
        ) : (
          <div className="text-slate-500 py-3 text-center italic">Run demodulator to inspect raw bitstream</div>
        )}
      </div>

      {/* Blind Interleaver Analysis */}
      {demodData?.interleaver_candidates && demodData.interleaver_candidates.length > 0 && (
        <div className="bg-slate-900/40 p-2 rounded border border-slate-800 flex items-center justify-between text-[10px] font-mono">
          <div className="flex items-center gap-1.5 text-purple-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>GF(2) INTERLEAVER SEARCH:</span>
          </div>
          <div className="text-slate-300">
            Detected Period <strong>M={demodData.interleaver_candidates[0].period}</strong> (Rank Defect {demodData.interleaver_candidates[0].rank_defect})
          </div>
        </div>
      )}
    </div>
  );
};
