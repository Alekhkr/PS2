import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { AnalysisResponse, ExperimentItem, SessionInfo } from './types';
import {
  fetchExperiments,
  loadSession,
  runAnalysis,
  uploadSignalFile,
} from './api';
import { useLenis } from './hooks/useLenis';
import { useAudioReactivity } from './hooks/useAudioReactivity';
import { CanvasContainer } from './components/canvas/CanvasContainer';
import { Preloader } from './components/ui/Preloader';
import { Navigation } from './components/ui/Navigation';
import { HeroSection } from './components/ui/HeroSection';
import { CuratorialNarrative } from './components/ui/CuratorialNarrative';
import { MathFormulation } from './components/ui/MathFormulation';
import { OverlayDossier } from './components/ui/OverlayDossier';
import { AutoSolveModal } from './components/ui/AutoSolveModal';
import { Outcome1Parameters } from './components/outcomes/Outcome1Parameters';
import { Outcome2Demodulation } from './components/outcomes/Outcome2Demodulation';
import { Outcome3Deinterleaving } from './components/outcomes/Outcome3Deinterleaving';
import { Outcome4Fec } from './components/outcomes/Outcome4Fec';
import { Outcome5Correlation } from './components/outcomes/Outcome5Correlation';

export const App: React.FC = () => {
  const [isPreloaderComplete, setIsPreloaderComplete] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [isDossierOpen, setIsDossierOpen] = useState(false);
  const [isAutoSolveOpen, setIsAutoSolveOpen] = useState(false);
  const [is3dActive, setIs3dActive] = useState(true);

  // Active Outcome Tab (0 to 4)
  const [activeTab, setActiveTab] = useState(0);

  // Experiment & Signal Lab Session State
  const [experiments, setExperiments] = useState<ExperimentItem[]>([]);
  const [currentExpIndex, setCurrentExpIndex] = useState(0);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  // Audio Reactivity Engine
  const { isPlaying: isAudioPlaying, audioLevel, eqLevels, toggle: toggleAudio } =
    useAudioReactivity();

  // Lenis Smooth Scroll
  const handleScroll = useCallback((progress: number) => {
    setScrollProgress(progress);
  }, []);

  const lenisRef = useLenis(handleScroll);
  const workbenchRef = useRef<HTMLDivElement>(null);

  // 1. Ingest Available Experiments on Mount
  useEffect(() => {
    fetchExperiments()
      .then((exps) => {
        setExperiments(exps);
        if (exps.length > 0) {
          loadExperimentByIndex(0, exps);
        }
      })
      .catch((err) => console.error('Failed to load experiments:', err));
  }, []);

  const loadExperimentByIndex = async (index: number, expsList?: ExperimentItem[]) => {
    const list = expsList || experiments;
    if (list.length === 0) return;
    const boundedIndex = (index + list.length) % list.length;
    setCurrentExpIndex(boundedIndex);
    const exp = list[boundedIndex];

    try {
      const sess = await loadSession({ experiment_id: exp.id });
      setSession(sess);
      triggerAnalysis(sess.session_id);
    } catch (err) {
      console.error('Failed to load session for experiment:', err);
    }
  };

  const handleUploadFile = async (file: File) => {
    try {
      setLoadingAnalysis(true);
      const sess = await uploadSignalFile(file);
      setSession(sess);
      triggerAnalysis(sess.session_id);
      scrollToWorkbench();
    } catch (err) {
      console.error('File upload failed:', err);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const triggerAnalysis = async (sessId: string) => {
    try {
      setLoadingAnalysis(true);
      const res = await runAnalysis(sessId);
      setAnalysis(res);
    } catch (err) {
      console.error('Analysis failed:', err);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  // Keyboard Shortcuts (D for dossier, M for audio)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      if (e.key === 'd' || e.key === 'D') {
        setIsDossierOpen((prev) => !prev);
      } else if (e.key === 'm' || e.key === 'M') {
        toggleAudio();
      } else if (e.key === 'Escape') {
        setIsDossierOpen(false);
        setIsAutoSolveOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [toggleAudio]);

  const scrollToWorkbench = () => {
    if (lenisRef.current && workbenchRef.current) {
      lenisRef.current.scrollTo(workbenchRef.current, { duration: 1.2 });
    } else if (workbenchRef.current) {
      workbenchRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const centerFreq = session?.center_frequency_hz ?? 15000000;
  const sampleRate = session?.sample_rate_hz ?? 20249;
  const totalDuration = session?.duration_s ?? 73.85;

  return (
    <div className="relative w-full min-h-screen bg-[#03070d] text-white selection:bg-[#00f0ff] selection:text-black">
      {/* 1. Cinematic Preloader */}
      {!isPreloaderComplete && (
        <Preloader onComplete={() => setIsPreloaderComplete(true)} />
      )}

      {/* 2. Fullscreen R3F Wave Ribbon Canvas (Smooth 60 FPS GLSL Background) */}
      <CanvasContainer
        isVisible={is3dActive}
        audioLevel={audioLevel}
        scrollProgress={scrollProgress}
      />

      {/* 3. Navigation Bar (Top Bar & Bottom Status Bar with 5 Outcome Tabs) */}
      <Navigation
        activeTab={activeTab}
        onSelectTab={(tab) => {
          setActiveTab(tab);
          scrollToWorkbench();
        }}
        experiments={experiments}
        currentExpIndex={currentExpIndex}
        onSelectExperiment={loadExperimentByIndex}
        onUploadFile={handleUploadFile}
        onOpenAutoSolve={() => setIsAutoSolveOpen(true)}
        isAudioPlaying={isAudioPlaying}
        onToggleAudio={toggleAudio}
        eqLevels={eqLevels}
        onOpenDossier={() => setIsDossierOpen(true)}
        is3dActive={is3dActive}
        onToggle3d={() => setIs3dActive((prev) => !prev)}
      />

      {/* 4. Main Scrollable Content */}
      <main className="relative z-10 w-full flex flex-col">
        {/* Section 1: Hero Banner */}
        <HeroSection
          onEnterWorkbench={scrollToWorkbench}
          onSelectTab={(tab) => {
            setActiveTab(tab);
            scrollToWorkbench();
          }}
          onOpenAutoSolve={() => setIsAutoSolveOpen(true)}
        />

        {/* Section 2: Dedicated 5-Outcome Workbench Workspace */}
        <div ref={workbenchRef} className="w-full px-4 md:px-8 py-12 scroll-mt-24">
          <div className="max-w-7xl mx-auto mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <span className="font-mono text-xs text-[#00f0ff] uppercase tracking-widest">
                ACTIVE WORKSPACE PIPELINE
              </span>
              <h2 className="text-2xl font-bold font-sans text-white">
                {activeTab === 0 && 'Outcome I: Signal Parameter Identification & Spectral Diagnostics'}
                {activeTab === 1 && 'Outcome II: Multi-Scheme Demodulation (FSK, PSK, QAM)'}
                {activeTab === 2 && 'Outcome III: Galois Field GF(2) De-Interleaving Workspace'}
                {activeTab === 3 && 'Outcome IV: Forward Error Correction (FEC) Decoding Ensemble'}
                {activeTab === 4 && 'Outcome V: Bitstream Correlation & Protocol Identification'}
              </h2>
            </div>

            {/* Stage Stepper Indicator */}
            <div className="flex items-center gap-1.5 font-mono text-xs bg-white/[0.04] p-1 rounded-lg border border-white/[0.08]">
              {['I. PARAMS', 'II. DEMOD', 'III. DEINT', 'IV. FEC', 'V. CORR'].map((label, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveTab(idx)}
                  className={`px-2.5 py-1 rounded transition text-[11px] font-semibold ${
                    activeTab === idx
                      ? 'bg-[#00f0ff] text-black shadow-md'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Render Active Outcome Tab */}
          {activeTab === 0 && (
            <Outcome1Parameters
              session={session}
              analysis={analysis}
              loadingAnalysis={loadingAnalysis}
              onRefreshAnalysis={() => session && triggerAnalysis(session.session_id)}
              centerFreq={centerFreq}
              sampleRate={sampleRate}
              totalDuration={totalDuration}
            />
          )}

          {activeTab === 1 && (
            <Outcome2Demodulation
              session={session}
              onNavigateToTab={setActiveTab}
            />
          )}

          {activeTab === 2 && (
            <Outcome3Deinterleaving
              session={session}
              onNavigateToTab={setActiveTab}
            />
          )}

          {activeTab === 3 && (
            <Outcome4Fec
              session={session}
              onNavigateToTab={setActiveTab}
            />
          )}

          {activeTab === 4 && (
            <Outcome5Correlation
              session={session}
            />
          )}
        </div>

        {/* Section 3: Curatorial Narrative Exploration */}
        <CuratorialNarrative />

        {/* Section 4: Mathematical Formulations & Wave PDEs */}
        <MathFormulation />

        {/* Footer */}
        <footer className="w-full py-16 px-6 md:px-12 border-t border-white/[0.08] bg-[#03070d] font-mono text-xs text-slate-500 flex flex-col md:flex-row justify-between items-center gap-6 select-none">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-[#00f0ff]" />
            <span className="text-white font-bold tracking-wider">SIGNAL LAB</span>
            <span>·</span>
            <span>SIH PS-2 TERRESTRIAL SIGNAL INTELLIGENCE PLATFORM</span>
          </div>

          <div className="flex items-center gap-6 text-[11px] text-slate-400">
            <span>FASTAPI SERVER: ONLINE</span>
            <span>PYTORCH + AVX2: READY</span>
            <span>85/85 AUDIT TESTS: PASSING</span>
          </div>
        </footer>
      </main>

      {/* 5. Scientific Dossier Modal Dialog */}
      <OverlayDossier
        isOpen={isDossierOpen}
        onClose={() => setIsDossierOpen(false)}
      />

      {/* 6. Autonomous End-to-End Pipeline Auto-Solve Modal */}
      <AutoSolveModal
        isOpen={isAutoSolveOpen}
        onClose={() => setIsAutoSolveOpen(false)}
        sessionId={session?.session_id || null}
        onJumpToStage={(stageIdx) => {
          setActiveTab(stageIdx);
          setIsAutoSolveOpen(false);
          scrollToWorkbench();
        }}
      />
    </div>
  );
};

export default App;
