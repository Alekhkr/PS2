import React, { useState } from 'react';
import type { AnalysisResponse, SessionInfo } from '../../types';
import { SmoothWaveform } from '../SmoothWaveform';
import { ConstellationView } from '../ConstellationView';
import { SpectrogramView } from '../SpectrogramView';
import { AnalysisPanel } from '../AnalysisPanel';
import { BitstreamInspector } from '../BitstreamInspector';

interface SignalLabDashboardProps {
  session: SessionInfo | null;
  analysis: AnalysisResponse | null;
  loadingAnalysis: boolean;
  onRefreshAnalysis: () => void;
  centerFreq: number;
  sampleRate: number;
  totalDuration: number;
}

export const SignalLabDashboard: React.FC<SignalLabDashboardProps> = ({
  session,
  analysis,
  loadingAnalysis,
  onRefreshAnalysis,
  centerFreq,
  sampleRate,
  totalDuration,
}) => {
  const [currentTime, setCurrentTime] = useState<number>(0.0);

  return (
    <section className="relative w-full py-32 px-8 md:px-16 z-10 border-t border-white/[0.06] bg-[#02050b] select-none">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-[#00f0ff] uppercase tracking-widest text-[11px] font-mono">
              <span className="w-2 h-2 rounded-full bg-[#00f0ff]" />
              <span>03 // SIGNAL LAB TELEMETRY & PHYSICAL AUDIT</span>
            </div>
            <h2 className="font-['Syne'] text-3xl sm:text-5xl font-extrabold text-white uppercase tracking-tight">
              60 FPS Level-of-Detail Engine
            </h2>
            <p className="text-base text-[#888888] font-light max-w-2xl font-sans leading-relaxed">
              Zero-lag multi-resolution Min-Max decimation allows buttery-smooth wheel zooming
              from entire recording buffers down to sub-microsecond pulse edges in real time.
            </p>
          </div>

          {/* Quick Hardware Badges */}
          <div className="flex items-center gap-3 font-mono text-xs">
            <div className="bg-black/60 border border-white/10 px-4 py-2 rounded-xl text-right">
              <div className="text-[10px] text-[#888888] uppercase">CENTER FREQ</div>
              <div className="text-white font-bold">{(centerFreq / 1e6).toFixed(3)} MHz</div>
            </div>
            <div className="bg-black/60 border border-white/10 px-4 py-2 rounded-xl text-right">
              <div className="text-[10px] text-[#888888] uppercase">SAMPLE RATE</div>
              <div className="text-[#00f0ff] font-bold">{(sampleRate / 1e6).toFixed(2)} MSps</div>
            </div>
          </div>
        </div>

        {/* 1. Full-Width 60 FPS Decimated Waveform */}
        <div className="w-full">
          <SmoothWaveform
            sessionId={session?.session_id ?? null}
            totalDuration={totalDuration}
            sampleRate={sampleRate}
            currentTime={currentTime}
            onTimeChange={setCurrentTime}
          />
        </div>

        {/* 2. Quad Diagnostics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Constellation & Spectrogram */}
          <div className="lg:col-span-6 flex flex-col gap-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <ConstellationView
                sessionId={session?.session_id ?? null}
                currentTime={currentTime}
                evmPercent={4.2}
                cumulantC40={-1.95}
                cumulantC42={0.98}
              />
              <SpectrogramView
                sessionId={session?.session_id ?? null}
                sampleRate={sampleRate}
                centerFreq={centerFreq}
              />
            </div>

            {/* Demodulation & Frame Sync */}
            <BitstreamInspector
              sessionId={session?.session_id ?? null}
              detectedMod={analysis?.modulation?.name}
            />
          </div>

          {/* Right Column: Hybrid AMC Modulation Classifier */}
          <div className="lg:col-span-6 flex flex-col gap-6">
            <AnalysisPanel
              analysis={analysis}
              loading={loadingAnalysis}
              onRefresh={onRefreshAnalysis}
            />
          </div>
        </div>
      </div>
    </section>
  );
};
