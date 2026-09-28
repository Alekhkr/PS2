import React from 'react';
import { BookOpen } from 'lucide-react';

export const CuratorialNarrative: React.FC = () => {
  return (
    <section className="relative w-full py-24 px-6 md:px-12 z-10 border-t border-white/[0.08] bg-[#03070d]/90 select-none">
      <div className="max-w-6xl mx-auto grid grid-cols-12 gap-8 md:gap-12">
        {/* Left Column */}
        <div className="col-span-12 lg:col-span-4 flex flex-col font-mono text-xs text-slate-400 space-y-4">
          <div className="flex items-center gap-2 text-[#00f0ff] uppercase tracking-widest text-[11px]">
            <BookOpen className="w-4 h-4" />
            <span>SCIENTIFIC NARRATIVE</span>
          </div>

          <h3 className="font-sans text-2xl font-bold text-white tracking-tight leading-tight">
            The Geometry of Wave Superposition
          </h3>

          <div className="space-y-2 pt-4 border-t border-white/10 text-xs text-slate-400 leading-relaxed font-sans">
            <div><strong className="text-white font-mono">DOMAIN:</strong> Terrestrial Radio Propagation (HF/VHF/UHF)</div>
            <div><strong className="text-white font-mono">CHANNELS:</strong> 15-Band Spatial Extruded Continuum</div>
            <div><strong className="text-white font-mono">THEORY:</strong> Multi-Harmonic Fourier Superposition</div>
          </div>
        </div>

        {/* Right Column */}
        <div className="col-span-12 lg:col-span-8 space-y-6 font-sans text-base text-slate-300 font-normal leading-relaxed">
          <p className="text-lg text-white font-medium leading-relaxed">
            In terrestrial radio propagation and high-frequency wavefields, captured signals are never isolated monoliths. They exist as an intricate superposition of oscillatory states, dispersing across atmospheric layers, diffracting around physical obstacles, and carrying critical modulation footprints.
          </p>

          <p>
            The <strong className="text-cyan-400 font-medium">Harmonic Wavefield Model</strong> represents this continuous electromagnetic spectrum. By synthesizing 15 spatial ribbon bands through a 4-mode Fourier expansion, the engine demonstrates how discrete phase shifts (Δθ = π/2) synthesize complex coherent signals from elementary sinusoidal building blocks. The localized Gaussian damping envelope, exp(-α·x²), enforces energy conservation at the resonant focal point.
          </p>

          {/* Pull Quote */}
          <div className="my-6 pl-5 border-l-2 border-[#00f0ff] py-1">
            <blockquote className="font-sans text-lg text-white font-medium italic leading-snug">
              “Continuous RF wavefields transform into actionable intelligence through automated blind estimation, robust carrier demodulation, and deterministic Galois Field error correction.”
            </blockquote>
            <span className="block font-mono text-xs text-slate-400 uppercase tracking-wider mt-2">
              — Signal Lab Technical Architecture
            </span>
          </div>

          <p>
            By coupling real-time GPU GLSL vertex displacement with scientific DSP kernels (AVX2-accelerated Viterbi, Berlekamp-Massey, and Min-Sum LDPC belief propagation), the system brings complete transparency to every stage of the RF reception chain.
          </p>
        </div>
      </div>
    </section>
  );
};
