import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { ArrowDown, Activity, Cpu, Layers, ShieldCheck, Binary, Zap } from 'lucide-react';

interface HeroSectionProps {
  onEnterWorkbench: () => void;
  onSelectTab: (tabIndex: number) => void;
  onOpenAutoSolve?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({
  onEnterWorkbench,
  onSelectTab,
  onOpenAutoSolve,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const tagRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const descRef = useRef<HTMLParagraphElement>(null);
  const pillsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ delay: 0.3 });

      tl.fromTo(
        tagRef.current,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' }
      )
        .fromTo(
          titleRef.current,
          { y: 30, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.9, ease: 'power3.out' },
          '-=0.5'
        )
        .fromTo(
          descRef.current,
          { y: 20, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.8, ease: 'power3.out' },
          '-=0.6'
        )
        .fromTo(
          pillsRef.current,
          { y: 20, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.8, ease: 'power3.out' },
          '-=0.5'
        );
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <section
      ref={containerRef}
      className="relative min-h-[85vh] w-full flex flex-col justify-center px-6 md:px-12 pt-32 pb-16 z-10 select-none"
    >
      <div className="w-full max-w-6xl mx-auto flex flex-col items-start gap-6">
        {/* Tag Pill */}
        <div ref={tagRef} className="flex items-center gap-3">
          <span className="font-mono text-[11px] font-bold tracking-widest text-[#00f0ff] uppercase px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-500/30">
            TERRESTRIAL RF SIGNAL ANALYZER
          </span>
          <span className="text-xs font-mono text-slate-400 tracking-wider hidden sm:inline">
            15-BAND HARMONIC TENSOR CONTINUUM
          </span>
        </div>

        {/* Clean Headline with Inter Typography */}
        <div className="overflow-hidden">
          <h1
            ref={titleRef}
            className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white font-sans leading-[1.08]"
          >
            Harmonic Wavefield &<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400">
              RF Intelligence Workbench
            </span>
          </h1>
        </div>

        {/* Crisp Subtitle */}
        <p
          ref={descRef}
          className="text-base sm:text-lg text-slate-300 max-w-2xl font-sans font-normal leading-relaxed"
        >
          An autonomous, GPU-accelerated signal intelligence platform. Ingests raw <code className="text-cyan-400 font-mono text-sm bg-white/[0.06] px-1.5 py-0.5 rounded">.IQ</code> and <code className="text-cyan-400 font-mono text-sm bg-white/[0.06] px-1.5 py-0.5 rounded">.WAV</code> captures, performs blind parameter extraction, demodulates multi-state constellations, executes Galois Field de-interleaving, and corrects transmission errors down to frame payloads.
        </p>

        {/* Quick Launch Buttons for the 5 Problem Statement Outcomes */}
        <div ref={pillsRef} className="flex flex-col gap-3 w-full pt-2">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-widest">
            DIRECT OUTCOME WORKSPACES:
          </span>
          <div className="flex flex-wrap items-center gap-2.5">
            {[
              { id: 0, label: 'I. Parameters & Spectrum', icon: Activity, color: 'text-cyan-400' },
              { id: 1, label: 'II. Demodulation (FSK/PSK/QAM)', icon: Cpu, color: 'text-purple-400' },
              { id: 2, label: 'III. De-Interleaving (GF2 Rank)', icon: Layers, color: 'text-emerald-400' },
              { id: 3, label: 'IV. FEC (Viterbi/RS/LDPC)', icon: ShieldCheck, color: 'text-amber-400' },
              { id: 4, label: 'V. Bitstream Correlation', icon: Binary, color: 'text-cyan-300' },
            ].map((out) => {
              const Icon = out.icon;
              return (
                <button
                  key={out.id}
                  onClick={() => {
                    onSelectTab(out.id);
                    onEnterWorkbench();
                  }}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.1] border border-white/[0.08] hover:border-cyan-500/40 text-xs font-sans text-slate-200 hover:text-white transition shadow-sm"
                >
                  <Icon className={`w-3.5 h-3.5 ${out.color}`} />
                  <span className="font-medium">{out.label}</span>
                </button>
              );
            })}
          </div>

          {/* Enter Workbench & Auto-Solve CTAs */}
          <div className="pt-4 flex flex-wrap items-center gap-4">
            <button
              onClick={onEnterWorkbench}
              className="flex items-center gap-2 px-6 py-3 rounded-full bg-[#00f0ff] hover:bg-cyan-300 text-black font-sans font-bold text-sm tracking-wide transition shadow-[0_0_25px_rgba(0,240,255,0.4)]"
            >
              <span>LAUNCH SIGNAL LAB WORKBENCH</span>
              <ArrowDown className="w-4 h-4" />
            </button>

            {onOpenAutoSolve && (
              <button
                onClick={onOpenAutoSolve}
                className="flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 border border-cyan-400 text-white font-sans font-bold text-sm tracking-wide transition shadow-[0_0_25px_rgba(0,240,255,0.35)]"
              >
                <Zap className="w-4 h-4 text-yellow-300 fill-yellow-300" />
                <span>⚡ 1-CLICK AUTO-SOLVE PIPELINE</span>
              </button>
            )}

            <span className="text-xs font-mono text-slate-500 hidden sm:inline">
              [Autonomous end-to-end signal intelligence]
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
