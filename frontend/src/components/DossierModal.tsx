import React from 'react';
import { X, BookOpen, CheckCircle, Code, Shield } from 'lucide-react';

interface DossierModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DossierModal: React.FC<DossierModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="austensor-panel w-full max-w-4xl max-h-[85vh] overflow-y-auto p-6 flex flex-col gap-6 relative border border-cyan-500/40 shadow-[0_0_50px_rgba(0,240,255,0.15)]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_10px_#00f0ff]" />
            <div>
              <h2 className="font-['Syne'] text-xl font-bold text-white uppercase tracking-wider">
                Scientific Dossier // Mathematical Formulation
              </h2>
              <p className="text-xs font-mono text-cyan-400">
                AUSTENSOR EXP_07 — AUDITABLE DSP & NEURAL SIGNAL SPECIFICATION
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          {/* Section 1: Min-Max Decimation */}
          <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-bold uppercase">
              <Code className="w-4 h-4" />
              1. 60 FPS LOD Min-Max Decimation
            </div>
            <p className="text-slate-300 font-sans leading-relaxed">
              Eliminates browser lag during wheel zoom by bounding draw primitives from
              <code className="text-amber-300"> N &gt; 10⁷ </code> down to fixed
              <code className="text-cyan-300"> B = 1200 </code> bins in vectorized NumPy:
            </p>
            <div className="bg-black/90 p-2.5 rounded text-cyan-300 font-mono text-[11px] overflow-x-auto">
              min_k = min(s[k·S : (k+1)·S])<br />
              max_k = max(s[k·S : (k+1)·S])
            </div>
            <p className="text-slate-400 text-[11px] font-sans">
              Payload size reduced from 160 MB to &lt; 5 KB, allowing instantaneous sub-millisecond zoom transitions.
            </p>
          </div>

          {/* Section 2: Higher Order Cumulants */}
          <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-purple-400 font-bold uppercase">
              <Shield className="w-4 h-4" />
              2. Higher-Order Cumulant Tensors
            </div>
            <p className="text-slate-300 font-sans leading-relaxed">
              Provides carrier-blind modulation classification by examining the 4th-order statistical moments:
            </p>
            <div className="bg-black/90 p-2.5 rounded text-purple-300 font-mono text-[11px] overflow-x-auto">
              C₄₀ = cum(y,y,y,y) = M₄₀ - 3(M₂₀)²<br />
              C₄₂ = cum(y,y,y*,y*) = M₄₂ - |M₂₀|² - 2(M₂₁)²
            </div>
            <p className="text-slate-400 text-[11px] font-sans">
              BPSK yields C₄₀ ≈ -2.0, QPSK yields C₄₀ ≈ -1.0, while 16QAM yields distinct multi-ring variance.
            </p>
          </div>

          {/* Section 3: Mueller-Muller Timing Recovery */}
          <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-emerald-400 font-bold uppercase">
              <BookOpen className="w-4 h-4" />
              3. Mueller-Müller Symbol Sync
            </div>
            <p className="text-slate-300 font-sans leading-relaxed">
              Recovers optimal sampling strobes at 1 sample per symbol without requiring baud rate oversampling:
            </p>
            <div className="bg-black/90 p-2.5 rounded text-emerald-300 font-mono text-[11px] overflow-x-auto">
              e_k = ℜ&#123; y_k · y*_(k-1) - y_(k-1) · y*_k &#125;<br />
              τ_(k+1) = τ_k + γ · e_k
            </div>
          </div>

          {/* Section 4: Blind Interleaver GF(2) Rank Defect */}
          <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-amber-400 font-bold uppercase">
              <CheckCircle className="w-4 h-4" />
              4. GF(2) Blind Interleaver Search
            </div>
            <p className="text-slate-300 font-sans leading-relaxed">
              Recovers matrix interleaver depth M without knowledge of code polynomial via Gaussian elimination over GF(2):
            </p>
            <div className="bg-black/90 p-2.5 rounded text-amber-300 font-mono text-[11px] overflow-x-auto">
              rank(Matrix_M) &lt; min(Rows, Cols)<br />
              Defect = min(N_r, N_c) - rank_GF2(M)
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center border-t border-white/10 pt-4 text-[11px] font-mono text-slate-400">
          <span>KEYBOARD SHORTCUTS: [D] DOSSIER · [M] HARMONIC AUDIO · [DOUBLE-CLICK] RESET ZOOM</span>
          <button
            onClick={onClose}
            className="austensor-btn text-white bg-cyan-600/30 border-cyan-400 hover:bg-cyan-500/50"
          >
            DISMISS DOSSIER
          </button>
        </div>
      </div>
    </div>
  );
};
