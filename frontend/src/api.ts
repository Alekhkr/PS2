import type {
  AnalysisResponse,
  ConstellationResponse,
  CorrelationResponse,
  DeinterleaveResponse,
  DemodulationResponse,
  ExperimentItem,
  FecDecodeResponse,
  SessionInfo,
  SpectrogramResponse,
  WaveformLodResponse,
} from './types';

const BASE_URL = '';

export async function fetchExperiments(): Promise<ExperimentItem[]> {
  const res = await fetch(`${BASE_URL}/api/experiments`);
  if (!res.ok) throw new Error(`Failed to fetch experiments: ${res.statusText}`);
  return res.json();
}

export async function loadSession(payload: {
  experiment_id?: string;
  file_path?: string;
  sample_rate?: number;
  center_freq?: number;
}): Promise<SessionInfo> {
  const res = await fetch(`${BASE_URL}/api/session/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Failed to load session');
  }
  return res.json();
}

export async function fetchWaveformLod(
  sessionId: string,
  startSec: number,
  endSec: number,
  targetPoints: number = 1200
): Promise<WaveformLodResponse> {
  const params = new URLSearchParams({
    session_id: sessionId,
    start_sec: startSec.toString(),
    end_sec: endSec.toString(),
    target_points: targetPoints.toString(),
  });
  const res = await fetch(`${BASE_URL}/api/waveform?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch waveform LOD: ${res.statusText}`);
  return res.json();
}

export async function fetchConstellation(
  sessionId: string,
  startSec: number = 0.0,
  endSec: number = 0.05,
  maxSymbols: number = 1024
): Promise<ConstellationResponse> {
  const params = new URLSearchParams({
    session_id: sessionId,
    start_sec: startSec.toString(),
    end_sec: endSec.toString(),
    max_symbols: maxSymbols.toString(),
  });
  const res = await fetch(`${BASE_URL}/api/constellation?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch constellation: ${res.statusText}`);
  return res.json();
}

export async function runAnalysis(sessionId: string): Promise<AnalysisResponse> {
  const params = new URLSearchParams({ session_id: sessionId });
  const res = await fetch(`${BASE_URL}/api/analyze?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to run analysis: ${res.statusText}`);
  return res.json();
}

export async function runDemodulation(
  sessionId: string,
  modType: string = 'BPSK'
): Promise<DemodulationResponse> {
  const params = new URLSearchParams({
    session_id: sessionId,
    mod_type: modType,
  });
  const res = await fetch(`${BASE_URL}/api/demodulate?${params.toString()}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Demodulation failed: ${res.statusText}`);
  return res.json();
}

export async function runDeinterleave(
  sessionId: string,
  method: string = 'block',
  rows: number = 8,
  cols: number = 8,
  period: number = 8
): Promise<DeinterleaveResponse> {
  const params = new URLSearchParams({
    session_id: sessionId,
    method,
    rows: rows.toString(),
    cols: cols.toString(),
    period: period.toString(),
  });
  const res = await fetch(`${BASE_URL}/api/deinterleave?${params.toString()}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`De-interleaving failed: ${res.statusText}`);
  return res.json();
}

export async function runFecDecode(
  sessionId: string,
  fecType: string = 'viterbi_conv'
): Promise<FecDecodeResponse> {
  const params = new URLSearchParams({
    session_id: sessionId,
    fec_type: fecType,
  });
  const res = await fetch(`${BASE_URL}/api/fec/decode?${params.toString()}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`FEC decoding failed: ${res.statusText}`);
  return res.json();
}

export async function runCorrelation(
  sessionId: string,
  patternName: string = 'Barker_13',
  threshold: number = 0.8
): Promise<CorrelationResponse> {
  const params = new URLSearchParams({
    session_id: sessionId,
    pattern_name: patternName,
    threshold: threshold.toString(),
  });
  const res = await fetch(`${BASE_URL}/api/correlate?${params.toString()}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Bitstream correlation failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSpectrogram(
  sessionId?: string,
  startSec: number = 0.0,
  endSec: number = 0.2,
  nFft: number = 512
): Promise<SpectrogramResponse> {
  const params = new URLSearchParams({
    start_sec: startSec.toString(),
    end_sec: endSec.toString(),
    n_fft: nFft.toString(),
  });
  if (sessionId) params.append('session_id', sessionId);
  const res = await fetch(`${BASE_URL}/api/spectrogram?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch spectrogram: ${res.statusText}`);
  return res.json();
}

export async function checkHealth(): Promise<{ status: string; active_sessions: number; dsp_kernels: string }> {
  const res = await fetch(`${BASE_URL}/api/health`);
  if (!res.ok) throw new Error(`Backend offline: ${res.statusText}`);
  return res.json();
}

export async function uploadSignalFile(file: File): Promise<SessionInfo> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`File upload failed: ${res.statusText}`);
  return res.json();
}
