import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Activity, Cpu, Sliders, ShieldCheck, Binary } from 'lucide-react';

interface OverlayDossierProps {
  isOpen: boolean;
  onClose: () => void;
}

export const OverlayDossier: React.FC<OverlayDossierProps> = ({ isOpen, onClose }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/85 backdrop-blur-2xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 10 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-4xl max-h-[88vh] overflow-y-auto bg-[#070d18] border border-cyan-500/30 rounded-2xl p-6 md:p-8 shadow-[0_0_80px_rgba(0,240,255,0.15)] select-none text-slate-300 font-sans"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-6">
              <div className="flex items-center gap-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#00f0ff] shadow-[0_0_12px_#00f0ff]" />
                <div>
                  <h2 className="text-xl font-bold text-white tracking-wide font-sans">
                    SIGNAL LAB // SCIENTIFIC ARCHITECTURE DOSSIER
                  </h2>
                  <div className="text-[11px] font-mono text-[#00f0ff] tracking-widest mt-0.5">
                    TERRESTRIAL RF SIGNAL ANALYSIS & PROTOCOL DECODING SPECIFICATIONS
                  </div>
                </div>
              </div>

              <button
                onClick={onClose}
                className="p-2 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                title="Dismiss Dossier (ESC)"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Grid Sections: 5 Problem Statement Outcomes */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
              {/* Box 1: Signal Parameters */}
              <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-xl space-y-2.5">
                <div className="flex items-center gap-2 text-[#00f0ff] font-bold uppercase tracking-wider font-mono">
                  <Activity className="w-4 h-4" />
                  <span>I. Signal Parameter Identification</span>
                </div>
                <p className="text-slate-400 font-sans leading-relaxed text-xs">
                  Extracts continuous signal features without prior synchronization:
                </p>
                <div className="bg-black/80 p-3 rounded border border-white/5 font-mono text-[11px] text-cyan-300 space-y-1">
                  <div>• Sampling Frequency: Automated Nyquist & bandwidth estimation</div>
                  <div>• Modulation AMC: 1D-ResNet deep learning + Cumulants (C₄₀, C₄₂)</div>
                  <div>• Carrier Offset (CFO): Sub-bin FFT peak interpolation</div>
                  <div>• Occupied Bandwidth: 99% cumulative power integral</div>
                  <div>• SNR Estimation: Higher-order moment ratio (M₂/M₄)</div>
                </div>
              </div>

              {/* Box 2: Demodulation */}
              <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-xl space-y-2.5">
                <div className="flex items-center gap-2 text-purple-400 font-bold uppercase tracking-wider font-mono">
                  <Cpu className="w-4 h-4" />
                  <span>II. Multi-Scheme Demodulation</span>
                </div>
                <p className="text-slate-400 font-sans leading-relaxed text-xs">
                  Carrier synchronization and hard-decision symbol recovery:
                </p>
                <div className="bg-black/80 p-3 rounded border border-white/5 font-mono text-[11px] text-purple-300 space-y-1">
                  <div>• FSK: FM frequency discriminator & 2/4-level slicer</div>
                  <div>• PSK: Costas loop carrier phase recovery (BPSK, QPSK)</div>
                  <div>• QAM: Automatic Gain Control (AGC) + 16/64-state grid slicer</div>
                  <div>• Slicer Diagnostics: Error Vector Magnitude (EVM %)</div>
                </div>
              </div>

              {/* Box 3: De-Interleaving */}
              <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-xl space-y-2.5">
                <div className="flex items-center gap-2 text-emerald-400 font-bold uppercase tracking-wider font-mono">
                  <Sliders className="w-4 h-4" />
                  <span>III. Galois Field De-Interleaving</span>
                </div>
                <p className="text-slate-400 font-sans leading-relaxed text-xs">
                  Reverses temporal bit permutation to disperse clustered channel errors:
                </p>
                <div className="bg-black/80 p-3 rounded border border-white/5 font-mono text-[11px] text-emerald-300 space-y-1">
                  <div>• Block De-interleaver: N×M matrix transposition</div>
                  <div>• Convolutional: Ramsey/Forney branched shift registers</div>
                  <div>• Diagonal: Cyclic diagonal step transposition</div>
                  <div>• Blind Rank Period Discovery: GF(2) matrix rank deficiency ΔR</div>
                </div>
              </div>

              {/* Box 4: FEC Decoding */}
              <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-xl space-y-2.5">
                <div className="flex items-center gap-2 text-amber-400 font-bold uppercase tracking-wider font-mono">
                  <ShieldCheck className="w-4 h-4" />
                  <span>IV. Forward Error Correction (FEC)</span>
                </div>
                <p className="text-slate-400 font-sans leading-relaxed text-xs">
                  Multi-architecture channel coding and parity verification:
                </p>
                <div className="bg-black/80 p-3 rounded border border-white/5 font-mono text-[11px] text-amber-300 space-y-1">
                  <div>• Viterbi: K=7, Rate 1/2, generators 171₈ / 133₈ trellis</div>
                  <div>• Reed-Solomon: RS(255, 223) Berlekamp-Massey in GF(2⁸)</div>
                  <div>• Concatenated: Inner Viterbi + Deinterleaver + Outer RS</div>
                  <div>• LDPC: IEEE 802.11n N=648, Rate 1/2 Min-Sum belief propagation</div>
                </div>
              </div>

              {/* Box 5: Bitstream Correlation */}
              <div className="md:col-span-2 bg-white/[0.02] border border-white/[0.08] p-5 rounded-xl space-y-2.5">
                <div className="flex items-center gap-2 text-[#00f0ff] font-bold uppercase tracking-wider font-mono">
                  <Binary className="w-4 h-4" />
                  <span>V. Bitstream Correlation & Header/Payload Isolation</span>
                </div>
                <p className="text-slate-400 font-sans leading-relaxed text-xs">
                  Sliding cross-correlation detects preamble sync markers (Barker-7/11/13, CCSDS ASM 0x1ACFFC1D, AX.25 Flag) and isolates transmission frame headers from user payload data for export.
                </p>
              </div>
            </div>

            {/* Footer Dismiss Note */}
            <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-slate-500">
              <span>PRESS [ESC] OR [D] TO DISMISS DOSSIER</span>
              <button
                onClick={onClose}
                className="text-white hover:text-cyan-400 font-bold transition-colors"
              >
                CLOSE DOSSIER [×]
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
