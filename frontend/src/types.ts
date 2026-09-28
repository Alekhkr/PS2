export interface ExperimentItem {
  id: string;
  name: string;
  band: string;
  format: string;
  sample_rate: number;
  center_freq: number;
  description: string;
  file: string;
}

export interface SessionInfo {
  session_id: string;
  filename: string;
  sample_rate_hz: number;
  center_frequency_hz: number;
  total_samples: number;
  duration_s: number;
}

export interface WaveformLodResponse {
  session_id?: string;
  mode: 'lod' | 'raw';
  time: number[];
  min_i?: number[];
  max_i?: number[];
  min_q?: number[];
  max_q?: number[];
  i?: number[];
  q?: number[];
  peak_amplitude?: number;
  rms_power?: number;
}

export interface SpectrogramResponse {
  session_id: string;
  frequencies: number[];
  times: number[];
  magnitude_db: number[][];
  sample_rate_hz: number;
}

export interface ConstellationResponse {
  session_id?: string;
  i: number[];
  q: number[];
}

export interface ModulationCandidateItem {
  name: string;
  score: number;
  validation: string;
}

export interface ModulationAnalysis {
  name: string;
  score: number;
  evidence: string[];
  candidates: ModulationCandidateItem[];
}

export interface AnalysisResponse {
  carrier_offset_hz: number;
  carrier_confidence: number;
  occupied_bw_hz: number;
  obw_confidence: number;
  snr_db: number;
  symbol_rate_baud: number;
  burst_count: number;
  modulation: ModulationAnalysis;
}

export interface SyncMatchItem {
  pattern: string;
  bit_index: number;
  score: number;
}

export interface InterleaverCandidateItem {
  period: number;
  rank_defect: number;
  confidence: number;
}

export interface DemodulationResponse {
  mod_type: string;
  evm_percent: number;
  bit_count: number;
  hard_bits_preview: number[];
  hex_preview: string;
  sync_matches: SyncMatchItem[];
  interleaver_candidates: InterleaverCandidateItem[];
}

export interface RankCurveItem {
  period: number;
  rank: number;
  defect: number;
}

export interface DeinterleaveResponse {
  method: string;
  input_bits_count: number;
  deinterleaved_preview: number[];
  hex_preview: string;
  rank_curve: RankCurveItem[];
  estimated_period: number;
}

export interface FecDecodeResponse {
  fec_type: string;
  name: string;
  syndrome_score: number;
  converged: boolean;
  errors_corrected: number;
  estimated_ber: number;
  decoded_bits_count: number;
  decoded_bits_preview: number[];
  hex_preview: string;
}

export interface CorrelationMatchDetail {
  offset_bits: number;
  score: number;
  pattern_length: number;
}

export interface CorrelationResponse {
  pattern_name: string;
  match_count: number;
  matches: CorrelationMatchDetail[];
  header_hex: string | null;
  payload_hex: string | null;
}
