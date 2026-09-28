export class HarmonicAudioEngine {
  private ctx: AudioContext | null = null;
  private isPlaying: boolean = false;
  private masterGain: GainNode | null = null;
  private analyser: AnalyserNode | null = null;
  private oscillators: OscillatorNode[] = [];
  private filter: BiquadFilterNode | null = null;

  public init() {
    if (this.ctx) return;
    const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    this.ctx = new AudioCtx();
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.setValueAtTime(0.0001, this.ctx.currentTime);

    this.analyser = this.ctx.createAnalyser();
    this.analyser.fftSize = 64;

    this.filter = this.ctx.createBiquadFilter();
    this.filter.type = 'lowpass';
    this.filter.frequency.setValueAtTime(450, this.ctx.currentTime);
    this.filter.Q.setValueAtTime(4.0, this.ctx.currentTime);

    this.masterGain.connect(this.filter);
    this.filter.connect(this.analyser);
    this.analyser.connect(this.ctx.destination);
  }

  public toggle(): boolean {
    this.init();
    if (!this.ctx || !this.masterGain) return false;

    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }

    if (this.isPlaying) {
      // Fade out
      this.masterGain.gain.setTargetAtTime(0.0001, this.ctx.currentTime, 0.08);
      setTimeout(() => {
        this.stopOscillators();
        this.isPlaying = false;
      }, 150);
      return false;
    } else {
      // Start harmonic oscillators: 55Hz, 110Hz, 165Hz, 220Hz
      this.startHarmonics([55.0, 110.0, 165.0, 220.0, 330.0]);
      this.masterGain.gain.setTargetAtTime(0.18, this.ctx.currentTime, 0.1);
      this.isPlaying = true;
      return true;
    }
  }

  public getActive(): boolean {
    return this.isPlaying;
  }

  private startHarmonics(frequencies: number[]) {
    if (!this.ctx || !this.masterGain) return;
    this.stopOscillators();

    frequencies.forEach((freq, idx) => {
      if (!this.ctx || !this.masterGain) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = idx % 2 === 0 ? 'sine' : 'triangle';
      osc.frequency.setValueAtTime(freq + (idx * 0.35), this.ctx.currentTime);

      const amp = 0.4 / (idx + 1);
      gain.gain.setValueAtTime(amp, this.ctx.currentTime);

      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start();
      this.oscillators.push(osc);
    });
  }

  private stopOscillators() {
    this.oscillators.forEach(osc => {
      try {
        osc.stop();
        osc.disconnect();
      } catch {
        // ignore already stopped
      }
    });
    this.oscillators = [];
  }

  public getEqualizerData(): number[] {
    if (!this.analyser || !this.isPlaying) {
      return [0, 0, 0, 0, 0, 0, 0, 0];
    }
    const data = new Uint8Array(8);
    this.analyser.getByteFrequencyData(data);
    return Array.from(data).map(v => v / 255);
  }
}

export const audioEngine = new HarmonicAudioEngine();
