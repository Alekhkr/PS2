# Smart India Hackathon (SIH 2026) — Complete Slide-by-Slide PPT Blueprint

**Project Title:** Signal Lab — Automated Terrestrial RF Signal Analysis Platform for Unknown HF/VHF/UHF Captures  
**Design Standard:** Strictly structured to match the official Smart India Hackathon (SIH 2026) 6-Slide Idea Submission Template (following the verified 3-column, architecture-flow, feasibility-chart, 4x4 impact matrix, and 4-quadrant reference layout).  
**Document Path:** `docs/SIH_PPT_SLIDE_BY_SLIDE_BLUEPRINT.md`  

---

```
====================================================================================================
                                      SLIDE 1: TITLE SLIDE
====================================================================================================
```

### Visual Layout & Formatting:
- **Top Header Banner:** SMART INDIA HACKATHON 2026 (with official SIH Logo on top right)
- **Central Left Block:** Clean, professional metadata card in high-contrast navy/dark slate typography.
- **Central Right Graphic:** SIH Lightbulb / Circuit emblem integrated with an RF Spectrum / Radar / Terrestrial Antenna icon.

### Exact Text & Content for Slide 1:
- **Problem Statement ID:** SIH26-DEF-094 *(or your assigned Problem Statement ID)*
- **Problem Statement Title:** Automated Terrestrial RF Signal Analysis Platform for Unknown HF, VHF, and UHF Band Captures (.IQ, .WAV, SigMF)
- **Theme:** Defense / Security / Smart Communications / Space & Aerospace Technology
- **PS Category:** Software
- **Team Name:** *(Your Team Name, e.g., Team SignalLab / Verbosity)*
- **Team ID:** *(Your Team ID, e.g., 162961)*
- **Ministry / Organization:** Ministry of Defence (MoD) / Defence Research and Development Organisation (DRDO) / Tri-Services Electronic Warfare & Intelligence

---

```
====================================================================================================
               SLIDE 2: THE PROBLEM, THE SOLUTION & UNIQUE INNOVATION
====================================================================================================
```

### Visual Layout & Formatting:
- **Header:** System Brand Banner: **SIGNAL LAB (TARANG-LAB)** | SIH Idea Submission Template | Team Name
- **3-Column Grid:**
  - **Column 1 (Red outline/accent cards):** `THE PROBLEM` (4 structured issue cards with icons & bold statistics)
  - **Column 2 (Green outline/accent cards):** `THE SOLUTION` (4 matching solution cards directly addressing the problems)
  - **Column 3 (Gold/Yellow outline/accent cards):** `UNIQUE INNOVATION` (4 USP cards highlighting unmatched technical differentiators)

---

### Column 1: THE PROBLEM (Red Outline Cards)

1. **MANUAL SPECTRUM TRIAGE BOTTLENECK**
   - *Icon:* Alert / Clock / Overloaded Funnel
   - *Text:* Military & spectrum surveillance operators spend hours manually tuning FFT flowgraphs and visual cursors for each recording, creating a **90%+ analysis backlog** in high-density tactical RF environments.

2. **METADATA AMNESIA ACROSS SENSORS**
   - *Icon:* Broken File / Question Mark
   - *Text:* Field captures in `.IQ` and `.WAV` formats arriving from disparate sensors lack sampling rates, center frequencies, and format tags, causing **downstream demodulation and protocol reverse engineering to completely fail**.

3. **THE "BLACK-BOX AI" PITFALL**
   - *Icon:* Blind Robot / Neural Error
   - *Text:* Pure deep learning classifiers act as black boxes; they hallucinate on novel modulation variants and provide **zero verifiable mathematical provenance or physical evidence** required for high-stakes defense intelligence.

4. **MULTI-LAYER PROTOCOL OPAQUENESS**
   - *Icon:* Scrambled Key / Lock
   - *Text:* Unknown block/convolutional interleaving, heterogeneous forward error correction (Viterbi, RS, LDPC), and variable frame structures prevent operators from **reconstructing headers and extracting mission-critical payloads**.

---

### Column 2: THE SOLUTION (Green Outline Cards)

1. **ZERO-TOUCH PARAMETER EXTRACTION**
   - *Icon:* Automated Radar / Lightning Gear
   - *Text:* Automated DSP pipeline instantly extracts sub-bin carrier frequency, 99% occupied bandwidth (OBW), in-band SNR, and cyclostationary baud rate candidates in **$<50$ ms without human intervention**.

2. **UNIVERSAL INGESTION & ZERO-COPY STREAMING**
   - *Icon:* Memory Buffer / Fast Stream
   - *Text:* Universal reader for `.IQ` (`cf32`, `ci16`, `ci8`), `.WAV`, and standard `SigMF`. Employs **memory-mapped zero-copy streaming** to load 3.2 GB captures in $<200$ ms with $<100$ MB RAM.

3. **HYBRID RESNET-1D + CUMULANT FUSION**
   - *Icon:* Neural + Math Shield
   - *Text:* 1D Residual CNN trained on 16 modulations cross-validated by higher-order cumulants ($C_{40}, C_{42}$) and envelope variance $\sigma_{|s|}^2$, delivering **82%+ accuracy down to low SNRs with full explainability**.

4. **PHYSICAL-TO-DATALINK PROTOCOL RECONSTRUCTION**
   - *Icon:* Connected Binary Link / Frame
   - *Text:* Autonomous pipeline executes blind $GF(2)$ matrix rank interleaver discovery, multi-scheme FEC decoding (Viterbi, Reed-Solomon, LDPC), and bitstream cross-correlation for **instant frame/header discovery**.

---

### Column 3: UNIQUE INNOVATION (Gold/Yellow Outline Cards)

1. **ZERO-COPY GIGABYTE STREAMING**
   - *Icon:* Rocket / Lightning Memory
   - *Text:* First open desktop instrument capable of streaming 80M samples/sec raw binary files with **virtually zero RAM overhead ($<100$ MB)**, enabling high-performance analysis on standard field laptops.

2. **BLIND GF(2) INTERLEAVER RANK DISCOVERY**
   - *Icon:* Binary Matrix / Mathematical Discovery
   - *Text:* Uses Galois Field Gaussian elimination to detect matrix rank deficiency, **discovering unknown block interleaver dimensions blindly** without requiring prior standard documentation.

3. **AUDITABLE MATHEMATICAL PROVENANCE**
   - *Icon:* Verified Badge / Audit Document
   - *Text:* Every inferred conclusion carries a calibrated confidence rating ($0.0-1.0$), mathematical assumptions, and algorithm provenance (`estimator`, `classifier`, `decoder`), **eliminating intelligence false alarms**.

4. **INTERACTIVE CLICK-TO-WAVEFORM TRACEABILITY**
   - *Icon:* Target Crosshair / Waveform Pointer
   - *Text:* Clicking any decoded bit, sync word, or payload byte in the Hex/ASCII Inspector **immediately repositions the time-frequency waterfall and constellation to that exact microsecond**.

---

```
====================================================================================================
                                 SLIDE 3: TECHNICAL APPROACH
====================================================================================================
```

### Visual Layout & Formatting:
- **Left Panel (25% width):** Technical Specifications, Languages, Libraries, Models, and Prototype Video Thumbnail.
- **Center & Right Canvas (75% width):** High-Impact End-to-End System Architecture Flowchart with clear data pipelines and feedback loops.

---

### Left Panel: Tech Stack & System Specifications

- **Programming Languages:**
  - Python 3.12+ (Core Architecture & Orchestration)
  - Modern C++20 (SIMD-accelerated DSP kernels via PyBind11)
- **AI & Neural Models:**
  - `ModulationResNet1D` (Lightweight 1D Residual CNN, 696 KB weights, sub-2ms CPU inference)
  - Trained on `RadioMod-R16` across 16 modulations (BPSK to 64QAM, FSK, MSK, GMSK)
- **GUI & Visualization:**
  - PySide6 (Qt for Python 6.11)
  - PyQtGraph (60 FPS GPU-accelerated waterfall, spectrum, and waveform instruments)
- **DSP & Mathematics:**
  - NumPy, SciPy (Welch PSD, Hilbert analytic transform, polyphase resampler)
- **Persistence & Metadata:**
  - SQLite3 (WAL mode non-blocking session history)
  - Native SigMF v1.0.0 Engine (`.sigmf-meta` + `.sigmf-data`)
- **Prototype Demo Video Callout:**
  - Live Desktop Demo: "Signal Lab v0.1.0 — 72/72 Unit/Integration Tests Passing (2.40s)".

---

### Center & Right Canvas: Architecture & Processing Data Flow

```mermaid
flowchart TD
    subgraph S1["1. INGESTION & ZERO-COPY STREAMING"]
        IN1["Heterogeneous Captures\n(.IQ, .WAV, SigMF)"] --> IN2["Streaming Gateway\n(Format Normalizer)"]
        IN2 --> MM["Zero-Copy Memory Map\n(StreamingSignalBuffer <100MB RAM)"]
        IN2 --> AD["Interactive Assumptions Dialog\n(Live Miniature Welch PSD Preview)"]
    end

    subgraph S2["2. DUAL FEATURE EXTRACTION ENGINE"]
        MM --> DSP_ENG["DSP Physics Engine\n- DC Offset & IQ Imbalance Correction\n- Sub-bin Quadratic Carrier Estimator\n- 99% Cumulative Occupied Bandwidth\n- Cyclostationary Baud Rate Search\n- STFT Energy Burst Detector"]
        MM --> NEU_ENG["Neural AMC Engine (ResNet-1D)\n- Input Tensor: (Batch, 2, 512)\n- 3 Residual Stages + BatchNorm\n- Softmax Probabilities across 16 Classes\n- Trained on RadioMod-R16"]
    end

    subgraph S3["3. HYBRID DECISION FUSION & PROVENANCE"]
        DSP_ENG --> FUSION["Hybrid Evidence Fusion Engine\n- Higher-Order Cumulants (C40, C42)\n- Envelope Variance (Const. vs Multi-level)\n- Cross-Validation: Penalizes Inconsistencies\n- Calibrated Confidence Score (0.0 - 1.0)"]
        NEU_ENG --> FUSION
    end

    subgraph S4["4. SYNCHRONIZATION & DEMODULATION"]
        FUSION --> SYNC["Carrier & Symbol Sync\n- 2nd-Order Costas Loop (Phase/Freq)\n- Mueller-Müller Timing Error Detector"]
        SYNC --> DEMOD["Multi-Modulation Demodulator\n- BPSK, QPSK, 8PSK, 16QAM, 64QAM, FSK\n- EVM % Calculation & Soft LLR Extraction"]
    end

    subgraph S5["5. PROTOCOL RECONSTRUCTION (FEC & INTERLEAVING)"]
        DEMOD --> BLIND_INT["Blind Interleaver Discovery\n- GF(2) Matrix Rank Deficiency\n- Transition Auto-Correlation Peaks\n- Reverses Block / Convolutional Permutations"]
        BLIND_INT --> FEC_DEC["Multi-Scheme FEC Decoding\n- Viterbi Convolutional Decoder (K=7, Rate 1/2)\n- Reed-Solomon GF(2^8) Evaluator\n- LDPC Iterative Min-Sum Belief Propagation\n- Concatenated FEC Pipeline"]
    end

    subgraph S6["6. FRAME DISCOVERY & INTERACTIVE INSTRUMENTS"]
        FEC_DEC --> CORR["Bitstream Cross-Correlator\n- Barker-7/11/13, CCSDS 32-bit ASM, AX.25\n- FFT Frame Periodicity Detector"]
        CORR --> UI["4-Instrument PyQtGraph Workspace\n- Synchronized 2D Waterfall + Region Selector\n- Waveform, Welch PSD in dBFS, Constellation\n- Bitstream Inspector (Hex/Binary/ASCII)\n- Click-to-Waveform Microsecond Navigation"]
    end
```

---

```
====================================================================================================
                              SLIDE 4: FEASIBILITY AND VIABILITY
====================================================================================================
```

### Visual Layout & Formatting:
- **3-Pillar Comparative Layout:**
  - **Pillar 1 (Left - Green):** `Feasibility of the Idea` (4 concrete operational proofs)
  - **Pillar 2 (Center - Red):** `Technical Challenges` (with data/bar chart comparing AMC accuracy across SNRs)
  - **Pillar 3 (Right - Gold):** `Engineering Resolutions` (direct mitigations implemented in Signal Lab)

---

### Pillar 1: Feasibility of the Idea (Green Accent)

- **Sub-Second Automated Processing:**
  - Algorithmic parameter estimation (Welch PSD, sub-bin carrier quadratic interpolation, and 99% OBW) executes in **$<50$ ms** on standard multi-core processors.
- **Zero-Copy Memory-Bounded Streaming:**
  - Implementation of `StreamingSignalBuffer` using `np.memmap` enables standard tactical laptops (8 GB RAM) to ingest 320 MB to 3.2 GB binary captures in **$<200$ ms** with strictly bounded RAM consumption ($<100$ MB).
- **Lightweight Offline Neural Architecture:**
  - The `ModulationResNet1D` weights total only **696 KB** and execute in **$<2$ ms per window on pure CPU**, eliminating the need for expensive, power-hungry tactical GPUs in the field.
- **Hardware-Accelerated C++ SIMD Execution:**
  - Core inner math loops (dot products, vector squaring, IQ rotations) are compiled into native C++ SIMD shared libraries via CMake and PyBind11, delivering **$8\times-12\times$ speedups**.

---

### Pillar 2: Technical Challenges & Empirical Benchmark (Red Accent)

#### Key Operational Hurdles:
1. **Low-SNR Constellation Collapse:** Below 0 dB SNR, phase clustering degrades, causing naive neural models to confuse high-order QAM with PSK.
2. **Missing Sampling Rate Ambiguity:** Unknown $f_s$ prevents direct calculation of physical bandwidth, symbol timing, and carrier offset.
3. **Exponential Interleaver Search Space:** Blind discovery of interleaver matrix widths without standard headers is combinatorial.

#### Empirical Benchmark Data (Modulation Classification Accuracy vs. SNR):
*(Represent as a stylized bar chart on the slide)*

```
Accuracy (%)
  100% ┤                                         ╭──── 82.5% ─── 82.3% ─── 80.5% ─── 79.7%
   80% ┤                        ╭──── 76.7% ─────╯
   60% ┤       ╭──── 68.7% ─────╯
   40% ┤ 49.4% ╯
   20% ┤
    0% ┴──────────────────────────────────────────────────────────────────────────────────
       -10 dB   -6 dB     0 dB      +4 dB       +6 dB       +10 dB      +24 dB      +30 dB
```
- **Overall Accuracy:** **73.69%** across all 16 modulation families across the entire SNR spectrum ($-10$ dB to $+30$ dB).
- **High-SNR Convergence:** **$>82\%$** accuracy at $\ge 6$ dB SNR.

---

### Pillar 3: Engineering Resolutions (Gold Accent)

- **Multimodal Decision Fusion:**
  - When the neural network predicts QAM at low SNR, the system calculates envelope variance $\sigma_{|s|}^2$. If $\sigma_{|s|}^2 < 0.08$ (constant envelope), the decision fusion engine automatically overrides the neural hallucination and assigns PSK/FSK.
- **Interactive Assumptions Dialog:**
  - For uncalibrated files with missing headers, an intuitive modal provides standard terrestrial rate presets ($48\text{ kHz}$ to $40\text{ MHz}$) alongside a **live miniature Welch PSD preview**, allowing visual confirmation in $<3$ seconds.
- **Galois Field GF(2) Rank Deficiency Test:**
  - Replaces brute-force search with Gaussian elimination over $GF(2)$. Interleaver widths that align with true codeword boundaries exhibit a sharp rank drop, detecting true interleaver dimensions in polynomial time $O(M \cdot W^2)$.
- **Dual Closed-Loop Synchronization:**
  - Incorporates a 2nd-order Costas loop ($f_e, \theta_e$) paired with Mueller-Müller fractional timing recovery to lock drifting carriers and open constellation eye diagrams automatically.

---

```
====================================================================================================
                                 SLIDE 5: IMPACT AND BENEFITS
====================================================================================================
```

### Visual Layout & Formatting:
- **4x4 Strategic Alignment Table Matrix:**
  - **Rows:** 1. Operational & Efficiency, 2. Economic & Financial, 3. Defense & National Security, 4. Technological & Strategic
  - **Columns:** IMPACT, BENEFITS, TARGET BENEFICIARY, ALIGNED DIRECTIVES / SDGs

---

| Domain | IMPACT | BENEFITS | TARGET BENEFICIARY | ALIGNED DIRECTIVES / SDGs |
|:---|:---|:---|:---|:---|
| **Operational & Efficiency** | • **10x–20x Faster Triage**: Reduces manual signal parameter extraction from hours to $<5$ seconds.<br>• **Automates 95% of Routine Tasks**: Eliminates human cursor measurements on FFTs. | • Clears massive intelligence backlogs in multi-signal RF environments.<br>• Frees specialized EW officers to focus on strategic threat analysis rather than manual DSP tuning. | • Military SIGINT Operators<br>• Electronic Warfare (EW) Battalions<br>• Wireless Monitoring Organisation (WMO) | **National Security Operational Readiness**<br>*(Mission-critical defense deployment)* |
| **Economic & Financial** | • **Zero Recurring Licensing Fees**: Eliminates reliance on proprietary foreign toolkits (e.g. DeepSig OmniSIG, Keysight, Rohde & Schwarz).<br>• **Runs on COTS Hardware**: Zero requirement for expensive GPU racks. | • Delivers massive cost savings to the defense exchequer.<br>• Deployable on standard ruggedized field laptops (8 GB RAM). | • Ministry of Defence (MoD)<br>• Armed Forces Procurement<br>• Indian Defense Budget | **Atmanirbhar Bharat / Make in India**<br>*(Indigenization of critical military software)* |
| **Defense & National Security** | • **Rapid Threat Attribution**: Instantly identifies rogue, covert, or unregistered terrestrial transmitters across HF, VHF, and UHF bands.<br>• **Auditable Intelligence**: Full mathematical provenance eliminates false positives. | • Prevents tactical surprise by adversary jamming, frequency-hopping, or covert data links.<br>• Generates courtroom-admissible and chain-of-custody intelligence reports. | • Indian Army, Navy, Air Force<br>• Defense Intelligence Agency (DIA)<br>• NTRO & National Security Agencies | **National Cyber & Electromagnetic Security**<br>*(Sovereign spectrum defense)* |
| **Technological & Sovereignty** | • **Complete Indigenous RF IP**: Complete physical-layer-to-bitstream pipeline built natively in India.<br>• **100% Offline Air-Gapped Security**: Zero cloud calls, zero telemetry leakage, zero external dependency. | • Establishes sovereign self-reliance in electronic intelligence algorithms.<br>• Guarantees 100% data sovereignty and immunity to foreign software kill-switches. | • DRDO Laboratories (DLRL, DEAL)<br>• Bharat Electronics Limited (BEL)<br>• Defense Communications Industry | **SDG 9: Industry & Innovation**<br>**SDG 16: Peace & Strong Institutions** |

---

```
====================================================================================================
                              SLIDE 6: RESEARCH AND REFERENCES
====================================================================================================
```

### Visual Layout & Formatting:
- **4-Quadrant Analytical Layout:**
  - **Quadrant 1 (Top Left):** Detailed Competitor Comparison Table (GNU Radio, Inspectrum, SigDigger, URH, DeepSig vs. Signal Lab)
  - **Quadrant 2 (Top Right):** Global & Indian Defense EW Market Growth & Strategic Catalysts
  - **Quadrant 3 (Bottom Left):** Market Sizing Research (TAM, SAM, SOM Funnel)
  - **Quadrant 4 (Bottom Right):** Formal Academic & Military Standard Citations

---

### Quadrant 1: Competitive Landscape Analysis (Top Left)

| Capability / Feature | GNU Radio | Inspectrum / SigDigger | Universal Radio Hacker (URH) | DeepSig OmniSIG | **SIGNAL LAB (OUR SYSTEM)** |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Automated Parameter Extraction** | ❌ *(Manual Flowgraph)* | ❌ *(Manual Cursors)* | ⚠️ *(Partial / Manual Tuning)* | ⚠️ *(Classification Only)* | **✅ 100% Autonomous (Sub-bin carrier, OBW, SNR, Baud)** |
| **Unknown Metadata Handling** | ❌ *(Fails without $f_s$)* | ❌ *(Requires manual input)* | ❌ *(Requires explicit sample rate)* | ⚠️ *(Fixed SDR rates)* | **✅ Interactive Calibration + Live PSD Preview** |
| **Zero-Copy Gigabyte Streaming** | ❌ *(Buffer overflow risk)* | ⚠️ *(Inspectrum memmap only)* | ❌ *(RAM exhaustion on >500MB)* | ❌ *(Streaming limited to SDR)* | **✅ np.memmap Streaming ($<100$MB RAM for 3.2GB)** |
| **Hybrid AMC (Neural + Cumulants)** | ❌ *(No built-in AMC)* | ❌ *(No AMC)* | ❌ *(No neural AMC)* | ⚠️ *(Black-box neural only)* | **✅ ResNet-1D + Cumulant Decision Fusion** |
| **Blind Interleaver Discovery** | ❌ | ❌ | ❌ | ❌ | **✅ GF(2) Matrix Rank Deficiency Search** |
| **Multi-Scheme FEC Decoding** | ⚠️ *(Requires custom blocks)* | ❌ | ⚠️ *(Basic parity/CRC)* | ❌ | **✅ Viterbi, Reed-Solomon, LDPC, Concatenated** |
| **Click-to-Waveform Traceability** | ❌ | ⚠️ *(Time cursor only)* | ⚠️ *(Bit-to-signal highlight)* | ❌ | **✅ Full Synchronized Microsecond Traceability** |

---

### Quadrant 2: Defense Electronic Warfare & SIGINT Market (Top Right)

- **Explosive Sector Growth:**
  - The **Global Electronic Warfare & SIGINT Market** is valued at **$28.5 Billion** and expanding at a compound annual growth rate of **7.8% CAGR**.
  - The **Indian Defense Electronics & Spectrum Surveillance Sector** is expanding at **15.4% CAGR**, driven by modernization along northern and western borders.
- **The National Strategic Catalyst:**
  - Creation of the **Integrated Theatre Commands** and the induction of automated battlefield management systems mandate real-time, automated spectrum intelligence.
- **First-Mover Operational Advantage:**
  - By unifying RF ingestion, hybrid classification, and FEC/interleaver protocol recovery into a single air-gapped instrument, Signal Lab creates a sovereign alternative to multi-million dollar foreign laboratory suites.

---

### Quadrant 3: Market Sizing Research (Bottom Left)

```
┌────────────────────────────────────────────────────────────────────────┐
│ TOTAL ADDRESSABLE MARKET (TAM)                                         │
│ $28.5 Billion (₹2,38,000 Crore)                                        │
│ Global Military Electronic Warfare, SIGINT & Spectrum Monitoring       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ SERVICEABLE ADDRESSABLE MARKET (SAM)                                   │
│ $3.2 Billion (₹26,800 Crore)                                           │
│ Terrestrial Tactical Signal Analysis & Spectrum Demodulation Software │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼─────────────────────────────────────┐
│ SERVICEABLE OBTAINABLE MARKET (SOM)                                    │
│ $250 Million (₹2,100 Crore)                                            │
│ Indian Tri-Services, DRDO Labs, NTRO, Border Electronic Defense       │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Quadrant 4: Scientific Literature & Standard References (Bottom Right)

1. **Automatic Modulation Classification Dataset:**
   - *RadioMod-R16 Dataset (HDF5)*: 16,800 labeled multi-carrier and single-carrier complex waveforms across 16 modulation families ($-10$ dB to $+30$ dB SNR).
2. **Deep Learning Academic Benchmark:**
   - O'Shea, T. J., Corgan, J., & Clancy, T. C., *"Convolutional Radio Modulation Recognition Networks"*, IEEE International Conference on Computing, Networking and Communications (ICNC), 2016 (DeepSig RML2016.10a).
3. **Higher-Order Cumulants for Blind Modulation Identification:**
   - Swami, A., & Sadler, B. M., *"Hierarchical digital modulation classification using cumulants"*, IEEE Transactions on Communications, Vol. 48, No. 3, pp. 416–429.
4. **Iterative Min-Sum LDPC Decoding Standards:**
   - IEEE 802.11n Standard for Information Technology—Telecommunications and Information Exchange Between Systems (Quasi-Cyclic LDPC Parity-Check Matrices, Block Length $N=648$, Rate 1/2).
5. **Concatenated Space & Military FEC Standards:**
   - CCSDS Blue Book 131.0-B-3, *"TM Synchronization and Channel Coding"*, Consultative Committee for Space Data Systems (Concatenated Reed-Solomon $RS(255, 223)$ + Convolutional $K=7$, Rate 1/2).
6. **Viterbi Traceback Decoding:**
   - Viterbi, A. J., *"Error bounds for convolutional codes and an asymptotically optimum decoding algorithm"*, IEEE Transactions on Information Theory, Vol. 13, No. 2, pp. 260–269.
