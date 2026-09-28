import React, { useRef, useState, useEffect } from 'react';
import type { ExperimentItem } from '../types';
import { audioEngine } from '../audio/AudioEngine';
import { Volume2, VolumeX, FileCode2, UploadCloud } from 'lucide-react';

interface TopNavProps {
  experiments: ExperimentItem[];
  selectedExpId: string;
  onSelectExperiment: (expId: string) => void;
  onUploadFile: (file: File) => void;
  onOpenDossier: () => void;
  centerFreq: number;
  sampleRate: number;
}

export const TopNav: React.FC<TopNavProps> = ({
  experiments,
  selectedExpId,
  onSelectExperiment,
  onUploadFile,
  onOpenDossier,
  centerFreq,
  sampleRate,
}) => {
  const [isAudioActive, setIsAudioActive] = useState(false);
  const [eqLevels, setEqLevels] = useState<number[]>([0.2, 0.4, 0.1, 0.5, 0.3, 0.6, 0.2, 0.4]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const toggleAudio = () => {
    const active = audioEngine.toggle();
    setIsAudioActive(active);
  };

  useEffect(() => {
    let animId = 0;
    const updateEq = () => {
      if (isAudioActive) {
        setEqLevels(audioEngine.getEqualizerData());
      }
      animId = requestAnimationFrame(updateEq);
    };
    animId = requestAnimationFrame(updateEq);
    return () => cancelAnimationFrame(animId);
  }, [isAudioActive]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUploadFile(e.target.files[0]);
    }
  };

  return (
    <header className="w-full bg-[#03070d]/90 backdrop-blur-md border-b border-white/[0.08] px-6 py-2.5 flex items-center justify-between z-30 select-none">
      {/* Brand & System Status */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#00f0ff] shadow-[0_0_10px_#00f0ff]" />
          <div>
            <div className="font-['Syne'] text-base font-extrabold tracking-wider text-white flex items-center gap-2">
              AUSTENSOR <span className="text-slate-500 font-light">//</span> SIGNAL LAB
            </div>
            <div className="text-[9px] font-mono text-slate-400 tracking-widest flex items-center gap-2">
              <span>EXP_07 WAVE OSCILLATION</span>
              <span className="text-emerald-400 flex items-center gap-1">
                <span className="pulse-emerald" /> 60 FPS
              </span>
            </div>
          </div>
        </div>

        {/* Experiment Selector Tabs */}
        <div className="hidden lg:flex items-center gap-1 bg-slate-950/80 p-1 rounded-lg border border-slate-800">
          {experiments.map((exp) => (
            <button
              key={exp.id}
              onClick={() => onSelectExperiment(exp.id)}
              className={`px-3 py-1 rounded text-[11px] font-mono transition-all ${
                selectedExpId === exp.id
                  ? 'bg-cyan-500/15 text-[#00f0ff] border border-cyan-500/40 shadow-[0_0_12px_rgba(0,240,255,0.25)] font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {exp.id.replace('exp_', '').replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Center Telemetry Readouts */}
      <div className="hidden md:flex items-center gap-4 text-right font-mono text-xs">
        <div>
          <div className="text-[9px] text-slate-500 uppercase">CENTER FREQUENCY</div>
          <div className="text-white font-bold">{(centerFreq / 1e6).toFixed(3)} MHz</div>
        </div>
        <div className="w-px h-6 bg-slate-800" />
        <div>
          <div className="text-[9px] text-slate-500 uppercase">SAMPLE RATE</div>
          <div className="text-[#00f0ff] font-bold">{(sampleRate / 1e6).toFixed(2)} MSps</div>
        </div>
      </div>

      {/* Action Triggers */}
      <div className="flex items-center gap-3">
        {/* Hidden File Input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".iq,.wav,.sigmf-meta,.sigmf-data"
          className="hidden"
        />

        <button
          onClick={() => fileInputRef.current?.click()}
          className="austensor-btn text-slate-300 hover:text-white"
          title="Upload .IQ, .WAV, or SigMF Dataset"
        >
          <UploadCloud className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">INGEST CAPTURE</span>
        </button>

        {/* Austensor Page 7 Harmonic Audio Resonance Toggle */}
        <button
          onClick={toggleAudio}
          className={`austensor-btn flex items-center gap-2 ${
            isAudioActive ? 'active text-[#00f0ff]' : 'text-slate-400'
          }`}
          title="Toggle Ionospheric Harmonic Resonance (Shortcut: M)"
        >
          {isAudioActive ? (
            <Volume2 className="w-3.5 h-3.5 text-[#00f0ff]" />
          ) : (
            <VolumeX className="w-3.5 h-3.5" />
          )}
          <span className="hidden sm:inline">HARMONIC PHASE</span>

          {/* Dancing Audio Equalizer */}
          <div className="flex items-end gap-0.5 h-3 ml-1">
            {eqLevels.map((lvl, i) => (
              <div
                key={i}
                className="w-0.5 bg-[#00f0ff] rounded-t-sm"
                style={{
                  height: isAudioActive ? `${Math.max(2, lvl * 12)}px` : '2px',
                  opacity: isAudioActive ? 0.9 : 0.25,
                }}
              />
            ))}
          </div>
        </button>

        {/* Mathematical Dossier Modal Button */}
        <button
          onClick={onOpenDossier}
          className="austensor-btn text-amber-300 hover:text-white border-amber-500/30"
          title="Austensor Scientific Proof Dossier (Shortcut: D)"
        >
          <FileCode2 className="w-3.5 h-3.5 text-amber-400" />
          <span>φ DOSSIER</span>
        </button>
      </div>
    </header>
  );
};
