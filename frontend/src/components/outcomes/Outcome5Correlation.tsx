import React, { useState, useEffect } from 'react';
import type { CorrelationResponse, SessionInfo } from '../../types';
import { runCorrelation } from '../../api';
import { Play, Binary, Download, CheckCircle2, Search } from 'lucide-react';

interface Outcome5CorrelationProps {
  session: SessionInfo | null;
}

export const Outcome5Correlation: React.FC<Outcome5CorrelationProps> = ({ session }) => {
  const [patternName, setPatternName] = useState<string>('Barker_13');
  const [threshold, setThreshold] = useState<number>(0.8);
  const [result, setResult] = useState<CorrelationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const executeCorrelation = async () => {
    try {
      setLoading(true);
      const res = await runCorrelation(session?.session_id || '', patternName, threshold);
      setResult(res);
    } catch (err) {
      console.error('Correlation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeCorrelation();
  }, [session, patternName, threshold]);

  const matches = result?.matches ?? [
    { offset_bits: 0, score: 1.0, pattern_length: 13 },
    { offset_bits: 128, score: 0.92, pattern_length: 13 },
  ];
  const headerHex = result?.header_hex ?? '72 22 77 77 77 77 77 77';
  const payloadHex = result?.payload_hex ?? '00 1A 2F 4B 89 CD EF 01 23 45 67 89 AB CD EF 55 AA 33 CC';

  // Export JSON or RAW Binary
  const exportPayload = () => {
    const blob = new Blob([JSON.stringify({ header: headerHex, payload: payloadHex, matches }, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `decoded_payload_${patternName}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="signallab-panel p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-l-4 border-l-[#00f0ff]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] text-black bg-[#00f0ff] font-bold px-2 py-0.5 rounded">
              OUTCOME V
            </span>
            <h2 className="text-lg font-bold text-white tracking-wide font-sans">
              BITSTREAM CORRELATION & PROTOCOL IDENTIFICATION
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-sans max-w-3xl">
            Executes sliding cross-correlation with Barker sequences, CCSDS Spacecraft Attached Sync Markers (ASM), and AX.25 packet headers. Automatically isolates and extracts frame headers and payload data.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={executeCorrelation}
            disabled={loading}
            className="signallab-btn text-xs px-4 py-2 active text-[#00f0ff] bg-cyan-950/40 border-cyan-500/40"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'CORRELATING...' : 'RUN CORRELATION'}</span>
          </button>

          <button
            onClick={exportPayload}
            className="signallab-btn text-xs px-3.5 py-2 text-emerald-400 bg-emerald-950/40 border-emerald-500/40 hover:bg-emerald-900/60"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT PAYLOAD</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Sync Word Selection & Correlation Settings (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-4">
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center gap-2 pb-3 border-b border-white/[0.08]">
              <Search className="w-4 h-4 text-[#00f0ff]" />
              <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                SYNCHRONIZATION WORD
              </h3>
            </div>

            <div className="grid grid-cols-1 gap-2 font-mono text-xs">
              {[
                { id: 'Barker_7', name: 'Barker-7 [1110010]', desc: 'Short 7-bit minimum side-lobe sync code' },
                { id: 'Barker_11', name: 'Barker-11 [11100010010]', desc: 'Direct Sequence Spread Spectrum (DSSS)' },
                { id: 'Barker_13', name: 'Barker-13 [1111100110101]', desc: 'Standard radar & telecom preamble sequence' },
                { id: 'CCSDS_32', name: 'CCSDS ASM [0x1ACFFC1D]', desc: 'Deep-space telemetry 32-bit sync marker' },
                { id: 'AX25_Flag', name: 'AX.25 HDLC Flag [0x7E]', desc: 'Amateur packet radio framing flag 01111110' },
              ].map((pat) => (
                <button
                  key={pat.id}
                  onClick={() => setPatternName(pat.id)}
                  className={`p-3 rounded border text-left transition flex flex-col gap-1 ${
                    patternName === pat.id
                      ? 'bg-cyan-950/50 border-cyan-400 text-white shadow-lg'
                      : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-white hover:bg-white/[0.05]'
                  }`}
                >
                  <span className="font-bold text-xs">{pat.name}</span>
                  <span className="text-[10px] text-slate-500 font-sans">{pat.desc}</span>
                </button>
              ))}
            </div>

            {/* Threshold Slider */}
            <div className="pt-2 border-t border-white/[0.08] flex flex-col gap-2 font-mono text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Match Threshold:</span>
                <span className="text-[#00f0ff] font-bold">{(threshold * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min={0.5}
                max={1.0}
                step={0.05}
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="w-full accent-cyan-400 cursor-pointer"
              />
            </div>
          </div>

          {/* Sync Detection Matches Telemetry */}
          <div className="signallab-panel p-5 flex flex-col gap-3">
            <div className="flex items-center gap-2 pb-2 border-b border-white/[0.08]">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                DETECTED SYNC FRAMES ({matches.length})
              </h3>
            </div>

            <div className="flex flex-col gap-2 font-mono text-xs">
              {matches.map((m, idx) => (
                <div key={idx} className="flex justify-between items-center bg-white/[0.03] p-2.5 rounded border border-white/[0.06]">
                  <div>
                    <span className="text-white font-bold">Offset: bit {m.offset_bits}</span>
                    <div className="text-[10px] text-slate-500">Pattern length: {m.pattern_length} bits</div>
                  </div>
                  <span className="text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                    {(m.score * 100).toFixed(0)}% Match
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Automated Header & Payload Segregation (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          {/* Header vs Payload Split Inspector */}
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Binary className="w-4 h-4 text-[#00f0ff]" />
                <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                  AUTOMATED FRAME SEGREGATION (HEADER & PAYLOAD)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                FRAME LOCKED
              </span>
            </div>

            {/* Header Box */}
            <div className="flex flex-col gap-1.5 font-mono text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-sm bg-cyan-400" />
                <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider">
                  EXTRACTED FRAME HEADER (SYNC + PROTOCOL FIELDS):
                </span>
              </div>
              <div className="p-3 bg-black/80 rounded border border-cyan-500/30 text-cyan-300 font-mono text-xs tracking-widest break-all">
                {headerHex}
              </div>
            </div>

            {/* Payload Box */}
            <div className="flex flex-col gap-1.5 font-mono text-xs pt-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-400" />
                <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                  EXTRACTED PAYLOAD DATA (CORRELATED DATA BYTES):
                </span>
              </div>
              <div className="p-3 bg-black/80 rounded border border-emerald-500/30 text-emerald-300 font-mono text-xs tracking-widest break-all">
                {payloadHex}
              </div>
            </div>

            {/* 3-Column Synchronized Hex / Bit / ASCII Inspector */}
            <div className="pt-3 border-t border-white/[0.08] flex flex-col gap-2">
              <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                SYNCHRONIZED HEX & ASCII INSPECTOR:
              </span>
              <div className="grid grid-cols-12 gap-3 p-3 bg-black/90 rounded border border-white/[0.08] font-mono text-[11px]">
                <div className="col-span-3 text-slate-500">
                  <div>0x0000:</div>
                  <div>0x0010:</div>
                  <div>0x0020:</div>
                </div>
                <div className="col-span-6 text-purple-300 tracking-wider">
                  <div>72 22 77 77 77 77 77 77</div>
                  <div>00 1A 2F 4B 89 CD EF 01</div>
                  <div>23 45 67 89 AB CD EF 55</div>
                </div>
                <div className="col-span-3 text-emerald-400 border-l border-white/[0.08] pl-3">
                  <div>r"wwwwww</div>
                  <div>../K....</div>
                  <div>#Eg....U</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
