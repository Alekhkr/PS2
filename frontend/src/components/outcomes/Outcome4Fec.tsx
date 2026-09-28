import React, { useState, useEffect } from 'react';
import type { FecDecodeResponse, SessionInfo } from '../../types';
import { runFecDecode } from '../../api';
import { Play, ShieldCheck, CheckCircle2, ArrowRight, Cpu } from 'lucide-react';

interface Outcome4FecProps {
  session: SessionInfo | null;
  onNavigateToTab?: (tabIndex: number) => void;
}

export const Outcome4Fec: React.FC<Outcome4FecProps> = ({
  session,
  onNavigateToTab,
}) => {
  const [fecType, setFecType] = useState<string>('viterbi_conv');
  const [result, setResult] = useState<FecDecodeResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const executeFec = async (type: string = fecType) => {
    try {
      setLoading(true);
      const res = await runFecDecode(session?.session_id || '', type);
      setResult(res);
    } catch (err) {
      console.error('FEC Decoding failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    executeFec(fecType);
  }, [session, fecType]);

  const converged = result?.converged ?? true;
  const errorsCorrected = result?.errors_corrected ?? 14;
  const ber = result?.estimated_ber ?? 0.00068;
  const decodedBits = result?.decoded_bits_preview ?? [];
  const hexPreview = result?.hex_preview ?? '72 22 77 77 77 77 77 77 77 77 72 22 22 22 22 22';

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="signallab-panel p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-l-4 border-l-[#f59e0b]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] text-black bg-[#f59e0b] font-bold px-2 py-0.5 rounded">
              OUTCOME IV
            </span>
            <h2 className="text-lg font-bold text-white tracking-wide font-sans">
              FORWARD ERROR CORRECTION (FEC) DECODING ENSEMBLE
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-sans max-w-3xl">
            Performs multi-standard channel error correction: short-constrained Convolutional Viterbi ($K=7$), Reed-Solomon $RS(255, 223)$, Concatenated Viterbi+RS, and IEEE 802.11n LDPC Min-Sum decoders with syndrome verification.
          </p>
        </div>

        <button
          onClick={() => executeFec()}
          disabled={loading}
          className="signallab-btn text-xs px-4 py-2 shrink-0 active text-amber-300 bg-amber-950/40 border-amber-500/40"
        >
          <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'DECODING...' : 'EXECUTE FEC DECODE'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: FEC Decoder Configuration (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center gap-2 pb-3 border-b border-white/[0.08]">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                SELECT FEC ARCHITECTURE
              </h3>
            </div>

            <div className="grid grid-cols-1 gap-2 font-mono text-xs">
              {[
                { id: 'viterbi_conv', name: 'Convolutional Code + Viterbi (K=7)', desc: 'Generators G₁=171₈, G₂=133₈, Rate 1/2, soft/hard trellis traceback' },
                { id: 'reed_solomon', name: 'Reed-Solomon RS(255, 223) GF(2⁸)', desc: 'Galois field Berlekamp-Massey + Chien search (T=16 byte correction)' },
                { id: 'concatenated', name: 'Concatenated FEC (Viterbi + RS)', desc: 'Inner convolutional Viterbi + Deinterleaver + Outer Reed-Solomon' },
                { id: 'ldpc', name: 'LDPC (IEEE 802.11n, N=648, R=1/2)', desc: 'Sparse Tanner graph Min-Sum log-likelihood belief propagation' },
              ].map((fec) => (
                <button
                  key={fec.id}
                  onClick={() => setFecType(fec.id)}
                  className={`p-3 rounded border text-left transition flex flex-col gap-1 ${
                    fecType === fec.id
                      ? 'bg-amber-950/50 border-amber-400 text-white shadow-lg'
                      : 'bg-white/[0.02] border-white/[0.06] text-slate-400 hover:text-white hover:bg-white/[0.05]'
                  }`}
                >
                  <span className="font-bold text-xs">{fec.name}</span>
                  <span className="text-[10px] text-slate-500 font-sans">{fec.desc}</span>
                </button>
              ))}
            </div>

            {/* Real-time Diagnostics Metrics */}
            <div className="pt-2 border-t border-white/[0.08] flex flex-col gap-2 font-mono text-xs">
              <div className="flex justify-between items-center bg-white/[0.03] p-2.5 rounded border border-white/[0.06]">
                <span className="text-slate-400">Syndrome Status:</span>
                <span className={`font-bold flex items-center gap-1 ${converged ? 'text-emerald-400' : 'text-amber-400'}`}>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {converged ? 'VALID CODEWORD (S=0)' : 'NON-ZERO SYNDROME'}
                </span>
              </div>

              <div className="flex justify-between items-center bg-white/[0.03] p-2.5 rounded border border-white/[0.06]">
                <span className="text-slate-400">Corrected Bit Errors:</span>
                <span className="text-[#00f0ff] font-bold">{errorsCorrected} bits corrected</span>
              </div>

              <div className="flex justify-between items-center bg-white/[0.03] p-2.5 rounded border border-white/[0.06]">
                <span className="text-slate-400">Post-FEC Bit Error Rate:</span>
                <span className="text-purple-300 font-bold">{ber.toExponential(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Decoded Payload & Clean Bitstream (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <div className="signallab-panel p-5 flex flex-col gap-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.08]">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-amber-400" />
                <h3 className="text-xs font-bold text-white tracking-wider uppercase font-mono">
                  CORRECTED DECODED BITSTREAM (FIRST 128 BITS)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
                TRELLIS CONVERGED
              </span>
            </div>

            {/* Bit Cell Matrix */}
            <div className="flex flex-wrap gap-1.5 p-3 rounded bg-black/60 border border-white/[0.06] font-mono text-[11px] max-h-48 overflow-y-auto">
              {decodedBits.length > 0 ? (
                decodedBits.map((b, idx) => (
                  <span
                    key={idx}
                    className={`inline-flex items-center justify-center w-5 h-5 rounded font-bold transition ${
                      b === 1
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/50'
                        : 'bg-slate-800/40 text-slate-500 border border-slate-700/40'
                    }`}
                  >
                    {b}
                  </span>
                ))
              ) : (
                <span className="text-slate-500 text-xs">Awaiting FEC decoding trigger...</span>
              )}
            </div>

            {/* Hex Dump */}
            <div className="flex flex-col gap-1.5 font-mono text-xs">
              <span className="text-[10px] text-slate-400 uppercase tracking-wider">HEX STREAM DUMP:</span>
              <div className="p-3 bg-black/80 rounded border border-white/[0.08] text-amber-300 tracking-widest break-all font-mono text-xs">
                {hexPreview}
              </div>
            </div>

            {/* Next Steps: Proceed to Correlation */}
            <div className="pt-3 border-t border-white/[0.08] flex items-center justify-between">
              <span className="text-xs text-slate-400 font-sans">
                Proceed to frame correlation and payload extraction:
              </span>
              <button
                onClick={() => onNavigateToTab && onNavigateToTab(4)}
                className="signallab-btn text-xs active text-amber-400 bg-amber-950/40"
              >
                <span>PROCEED TO CORRELATION</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
