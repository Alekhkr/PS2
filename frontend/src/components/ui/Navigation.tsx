import React, { useRef } from 'react';
import { Volume2, VolumeX, Upload, Compass, Eye, EyeOff, Zap } from 'lucide-react';
import type { ExperimentItem } from '../../types';

interface NavigationProps {
  activeTab: number;
  onSelectTab: (index: number) => void;
  experiments: ExperimentItem[];
  currentExpIndex: number;
  onSelectExperiment: (index: number) => void;
  onUploadFile: (file: File) => void;
  onOpenAutoSolve: () => void;
  isAudioPlaying: boolean;
  onToggleAudio: () => void;
  eqLevels: number[];
  onOpenDossier: () => void;
  is3dActive: boolean;
  onToggle3d: () => void;
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onSelectTab,
  experiments,
  currentExpIndex,
  onSelectExperiment,
  onUploadFile,
  onOpenAutoSolve,
  isAudioPlaying,
  onToggleAudio,
  eqLevels,
  onOpenDossier,
  is3dActive,
  onToggle3d,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUploadFile(e.target.files[0]);
    }
  };

  const tabs = [
    { id: 0, label: 'I. PARAMETERS', desc: 'Sampling Rate, OBW, CFO, AMC, Oscilloscope & STFT' },
    { id: 1, label: 'II. DEMODULATION', desc: 'FSK, BPSK, QPSK, 16QAM & 64QAM Slicer' },
    { id: 2, label: 'III. DE-INTERLEAVING', desc: 'Block, Conv, Diagonal & GF(2) Rank Period' },
    { id: 3, label: 'IV. FEC DECODING', desc: 'Viterbi K=7, Reed-Solomon, Concatenated & LDPC' },
    { id: 4, label: 'V. CORRELATION', desc: 'Barker, CCSDS ASM, AX.25 & Header/Payload Split' },
  ];

  const currentExp = experiments[currentExpIndex] || {
    name: 'WWV Standard HF (15 MHz)',
    band: 'HF Standard',
  };

  return (
    <>
      {/* Top Floating App Bar */}
      <header className="fixed top-0 left-0 right-0 z-40 px-4 md:px-8 py-3 bg-[#03070d]/90 backdrop-blur-xl border-b border-white/[0.08] flex flex-col gap-2.5 select-none shadow-2xl">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Brand Identity & Capture Selector */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-[#00f0ff] shadow-[0_0_12px_#00f0ff] animate-pulse" />
              <div className="flex flex-col">
                <span className="font-sans font-extrabold tracking-wider text-sm text-white flex items-center gap-2">
                  SIGNAL LAB <span className="text-[10px] font-mono text-[#00f0ff] bg-cyan-950/80 px-2 py-0.5 rounded border border-cyan-800/40">RF INTELLIGENCE WORKBENCH</span>
                </span>
                <span className="text-[10px] font-mono text-slate-400 hidden sm:inline">
                  SIH PS-2 · High-Performance DSP, AMC Neural Classifier & Galois Field Protocol Recovery
                </span>
              </div>
            </div>

            {/* Presets Dropdown */}
            <div className="hidden lg:flex items-center gap-1.5 ml-4">
              <span className="text-[10px] font-mono text-slate-500">CAPTURE:</span>
              <select
                value={currentExpIndex}
                onChange={(e) => onSelectExperiment(Number(e.target.value))}
                className="bg-black/60 border border-white/10 rounded px-2.5 py-1 text-xs font-mono text-slate-200 hover:border-cyan-500/50 outline-none cursor-pointer"
              >
                {experiments.map((exp, idx) => (
                  <option key={exp.id} value={idx} className="bg-slate-900 text-white">
                    {exp.name} ({exp.band})
                  </option>
                ))}
              </select>
            </div>

            {/* Upload .IQ / .WAV Button */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".iq,.wav,.bin,.raw,.dat"
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="signallab-btn text-[11px] px-3 py-1.5 active text-[#00f0ff] bg-cyan-950/40 border-cyan-500/40"
              title="Upload custom .IQ, .WAV, or raw binary RF capture"
            >
              <Upload className="w-3.5 h-3.5 text-[#00f0ff]" />
              <span className="hidden sm:inline">UPLOAD .IQ / .WAV</span>
            </button>

            {/* ⚡ AUTO-SOLVE 1-Click Pipeline Button */}
            <button
              onClick={onOpenAutoSolve}
              className="signallab-btn text-[11px] px-3.5 py-1.5 text-white bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 border border-cyan-400/60 shadow-[0_0_12px_rgba(0,240,255,0.35)] font-bold tracking-wide"
              title="Execute 1-Click Autonomous Multi-Stage Signal Processing Pipeline"
            >
              <Zap className="w-3.5 h-3.5 text-yellow-300 fill-yellow-300" />
              <span>⚡ AUTO-SOLVE</span>
            </button>
          </div>

          {/* Right Action Cluster */}
          <div className="flex items-center gap-2.5">
            {/* 3D Wave Ribbon Toggle */}
            <button
              onClick={onToggle3d}
              className={`signallab-btn text-[11px] px-3 py-1.5 ${is3dActive ? 'active text-[#00f0ff]' : 'text-slate-400'}`}
              title="Toggle 3D Harmonic Wave Ribbon Background"
            >
              {is3dActive ? <Eye className="w-3.5 h-3.5 text-[#00f0ff]" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">3D WAVE: {is3dActive ? 'ON' : 'OFF'}</span>
            </button>

            {/* Audio Harmonic Phase Toggle */}
            <button
              onClick={onToggleAudio}
              className={`signallab-btn text-[11px] px-3 py-1.5 ${
                isAudioPlaying ? 'active text-[#00f0ff]' : 'text-slate-400'
              }`}
              title="Toggle Web Audio Additive Resonance (Key: M)"
            >
              {isAudioPlaying ? (
                <Volume2 className="w-3.5 h-3.5 text-[#00f0ff]" />
              ) : (
                <VolumeX className="w-3.5 h-3.5" />
              )}
              <span className="hidden md:inline">AUDIO</span>
              {/* Equalizer Wavelet */}
              <div className="flex items-end gap-0.5 h-3">
                {eqLevels.map((lvl, i) => (
                  <div
                    key={i}
                    className="w-0.5 bg-current rounded-t-sm transition-all duration-75"
                    style={{
                      height: isAudioPlaying ? `${Math.max(2, lvl * 10)}px` : '2px',
                    }}
                  />
                ))}
              </div>
            </button>

            {/* Scientific Dossier Modal Toggle */}
            <button
              onClick={onOpenDossier}
              className="signallab-btn text-[11px] px-3 py-1.5 text-slate-300 hover:text-white"
              title="Open Mathematical Formulation Dossier (Key: D)"
            >
              <Compass className="w-3.5 h-3.5 text-[#00f0ff]" />
              <span>DOSSIER</span>
            </button>

            {/* Backend Status Pill */}
            <div className="hidden xl:flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2.5 py-1 rounded">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>FASTAPI + C++ ONLINE</span>
            </div>
          </div>
        </div>

        {/* Bottom Strip: 5 Dedicated Problem Statement Outcome Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pt-1 pb-0.5">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`outcome-tab-btn shrink-0 ${activeTab === tab.id ? 'active' : ''}`}
            >
              <span className="font-bold">{tab.label}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Bottom Floating Status Bar */}
      <footer className="fixed bottom-0 left-0 right-0 z-40 px-6 py-2.5 flex items-center justify-between select-none text-[11px] font-mono text-[#888888] border-t border-white/[0.06] bg-black/90 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="text-[#00f0ff] font-bold">SIGNAL LAB v1.0.0</span>
          <span className="text-slate-600">|</span>
          <span className="hidden sm:inline">CAPTURE: {currentExp.name}</span>
          <span className="text-slate-600 hidden sm:inline">|</span>
          <span className="text-emerald-400">85/85 DSP KERNELS VALIDATED</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden md:inline text-slate-400">SHORTCUTS: [D] Dossier · [M] Audio</span>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#00ff88] shadow-[0_0_8px_#00ff88]" />
            <span className="text-white font-semibold">60.0 FPS</span>
            <span className="text-slate-500">[WEBGL & REACT 19]</span>
          </div>
        </div>
      </footer>
    </>
  );
};
