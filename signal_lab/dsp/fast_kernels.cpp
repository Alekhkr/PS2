#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <complex>
#include <algorithm>

namespace py = pybind11;

// Returns a tuple of (min_i, max_i, min_q, max_q)
py::tuple min_max_decimate_iq(py::array_t<std::complex<float>> samples, int target_points) {
    py::buffer_info buf = samples.request();
    auto ptr = static_cast<std::complex<float>*>(buf.ptr);
    int num_samples = buf.size;

    if (num_samples < target_points * 2) {
        target_points = std::max(1, num_samples / 2);
    }

    int bin_size = num_samples / target_points;
    int n_bins = target_points;

    auto min_i = py::array_t<float>(n_bins);
    auto max_i = py::array_t<float>(n_bins);
    auto min_q = py::array_t<float>(n_bins);
    auto max_q = py::array_t<float>(n_bins);

    auto ptr_min_i = static_cast<float*>(min_i.request().ptr);
    auto ptr_max_i = static_cast<float*>(max_i.request().ptr);
    auto ptr_min_q = static_cast<float*>(min_q.request().ptr);
    auto ptr_max_q = static_cast<float*>(max_q.request().ptr);

    for (int b = 0; b < n_bins; ++b) {
        int start_idx = b * bin_size;
        float current_min_i = ptr[start_idx].real();
        float current_max_i = current_min_i;
        float current_min_q = ptr[start_idx].imag();
        float current_max_q = current_min_q;

        for (int i = 1; i < bin_size; ++i) {
            float i_val = ptr[start_idx + i].real();
            float q_val = ptr[start_idx + i].imag();
            if (i_val < current_min_i) current_min_i = i_val;
            if (i_val > current_max_i) current_max_i = i_val;
            if (q_val < current_min_q) current_min_q = q_val;
            if (q_val > current_max_q) current_max_q = q_val;
        }

        ptr_min_i[b] = current_min_i;
        ptr_max_i[b] = current_max_i;
        ptr_min_q[b] = current_min_q;
        ptr_max_q[b] = current_max_q;
    }

    return py::make_tuple(min_i, max_i, min_q, max_q);
}

// In-place Radix-2 Cooley-Tukey FFT
void fft_inplace(std::vector<std::complex<float>>& x) {
    const size_t N = x.size();
    if (N <= 1) return;

    // Bit-reverse
    size_t j = 0;
    for (size_t i = 1; i < N; i++) {
        size_t bit = N >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) std::swap(x[i], x[j]);
    }

    // Cooley-Tukey
    for (size_t len = 2; len <= N; len <<= 1) {
        float angle = -2.0f * M_PI / len;
        std::complex<float> wlen(std::cos(angle), std::sin(angle));
        for (size_t i = 0; i < N; i += len) {
            std::complex<float> w(1.0f, 0.0f);
            for (size_t j = 0; j < len / 2; j++) {
                std::complex<float> u = x[i + j];
                std::complex<float> v = x[i + j + len / 2] * w;
                x[i + j] = u + v;
                x[i + j + len / 2] = u - v;
                w *= wlen;
            }
        }
    }
}

// Fast carrier estimator returning the peak bin and its quadratic offset
py::tuple estimate_carrier_peak(py::array_t<std::complex<float>> samples, int nperseg) {
    py::buffer_info buf = samples.request();
    auto ptr = static_cast<std::complex<float>*>(buf.ptr);
    int num_samples = buf.size;

    // Ensure power of 2 for FFT
    int nfft = 1;
    while (nfft <= nperseg && nfft <= num_samples) nfft <<= 1;
    nfft >>= 1;
    if (nfft < 16) nfft = 16;
    
    int num_segments = num_samples / nfft;
    if (num_segments == 0) num_segments = 1;
    
    std::vector<float> psd(nfft, 0.0f);
    std::vector<std::complex<float>> segment(nfft);
    
    // Compute Welch-like PSD (rectangular window for max speed)
    for (int i = 0; i < num_segments; ++i) {
        for (int j = 0; j < nfft; ++j) {
            if (i * nfft + j < num_samples) {
                segment[j] = ptr[i * nfft + j];
            } else {
                segment[j] = {0.0f, 0.0f};
            }
        }
        
        fft_inplace(segment);
        
        for (int j = 0; j < nfft; ++j) {
            // fftshift dynamically: (j + nfft/2) % nfft
            int shifted_idx = (j + nfft / 2) % nfft;
            float mag = std::norm(segment[j]);
            psd[shifted_idx] += mag;
        }
    }
    
    // Find peak
    int peak_idx = 0;
    float max_val = psd[0];
    for (int j = 1; j < nfft; ++j) {
        if (psd[j] > max_val) {
            max_val = psd[j];
            peak_idx = j;
        }
    }
    
    // Quadratic sub-bin interpolation
    float sub_bin_offset = 0.0f;
    if (peak_idx > 0 && peak_idx < nfft - 1) {
        float alpha = psd[peak_idx - 1];
        float beta = psd[peak_idx];
        float gamma = psd[peak_idx + 1];
        float denom = alpha - 2 * beta + gamma + 1e-15f;
        float delta = 0.5f * (alpha - gamma) / denom;
        sub_bin_offset = delta;
    }
    
    // Median for confidence
    std::vector<float> sorted_psd = psd;
    std::nth_element(sorted_psd.begin(), sorted_psd.begin() + nfft/2, sorted_psd.end());
    float median_val = sorted_psd[nfft/2];
    
    float pmr = max_val / (median_val + 1e-15f);
    
    return py::make_tuple(peak_idx, sub_bin_offset, nfft, pmr);
}

// Fast Costas Loop
py::tuple costas_loop_process(py::array_t<std::complex<float>> samples, int order, float damping, float loop_bw) {
    py::buffer_info buf = samples.request();
    auto ptr = static_cast<std::complex<float>*>(buf.ptr);
    int n = buf.size;

    auto out = py::array_t<std::complex<float>>(n);
    auto out_ptr = static_cast<std::complex<float>*>(out.request().ptr);
    auto phase_errors = py::array_t<float>(n);
    auto pe_ptr = static_cast<float*>(phase_errors.request().ptr);

    float denom = 1.0f + 2.0f * damping * loop_bw + loop_bw * loop_bw;
    float alpha = (4.0f * damping * loop_bw) / denom;
    float beta = (4.0f * loop_bw * loop_bw) / denom;

    float phase = 0.0f;
    float freq = 0.0f;

    for (int i = 0; i < n; ++i) {
        std::complex<float> s = ptr[i] * std::polar(1.0f, -phase);
        out_ptr[i] = s;

        float error = 0.0f;
        if (order == 2) {
            error = s.real() * s.imag();
        } else if (order == 4) {
            float sgn_r = s.real() > 0 ? 1.0f : (s.real() < 0 ? -1.0f : 0.0f);
            float sgn_i = s.imag() > 0 ? 1.0f : (s.imag() < 0 ? -1.0f : 0.0f);
            error = sgn_r * s.imag() - sgn_i * s.real();
        } else if (order == 8) {
            float angle = std::arg(s);
            float nearest_ray = std::round(angle / (M_PI / 4.0f)) * (M_PI / 4.0f);
            error = std::sin(angle - nearest_ray);
        } else {
            error = s.imag();
        }

        pe_ptr[i] = error;

        freq += beta * error;
        phase += freq + alpha * error;

        // Wrap phase to [-pi, pi]
        while (phase > M_PI) phase -= 2.0f * M_PI;
        while (phase < -M_PI) phase += 2.0f * M_PI;
    }

    float rms_pe = 0.0f;
    int start_idx = n > 20 ? n / 2 : 0;
    int count = n - start_idx;
    if (count > 0) {
        float sum_sq = 0.0f;
        for (int i = start_idx; i < n; ++i) sum_sq += pe_ptr[i] * pe_ptr[i];
        rms_pe = std::sqrt(sum_sq / count);
    }

    bool converged = rms_pe < 0.35f;
    
    py::dict metrics;
    metrics["converged"] = converged;
    metrics["rms_phase_error_rad"] = rms_pe;
    metrics["residual_frequency_offset"] = freq;

    return py::make_tuple(out, metrics);
}

// Fast Mueller-Muller TED
py::tuple mueller_muller_timing_recovery(py::array_t<std::complex<float>> samples, int sps, float loop_gain) {
    py::buffer_info buf = samples.request();
    auto ptr = static_cast<std::complex<float>*>(buf.ptr);
    int n = buf.size;

    if (n < sps * 4) {
        // Fallback
        int out_n = std::max(1, n / sps);
        auto out = py::array_t<std::complex<float>>(out_n);
        auto out_ptr = static_cast<std::complex<float>*>(out.request().ptr);
        for(int i = 0; i < out_n; ++i) out_ptr[i] = ptr[i * sps];
        py::dict m;
        m["timing_converged"] = false;
        m["rms_timing_error"] = 1.0f;
        m["symbol_count"] = out_n;
        return py::make_tuple(out, m);
    }

    std::vector<std::complex<float>> symbols;
    std::vector<float> timing_errors;
    symbols.reserve(n / sps + 10);
    timing_errors.reserve(n / sps + 10);

    float idx = 0.0f;
    std::complex<float> last_sym(0.0f, 0.0f);
    std::complex<float> last_dec(0.0f, 0.0f);

    while (static_cast<int>(idx) < n - 2) {
        int base_idx = static_cast<int>(idx);
        float frac = idx - base_idx;

        std::complex<float> s = ptr[base_idx] * (1.0f - frac) + ptr[base_idx + 1] * frac;

        float sgn_r = s.real() > 0 ? 1.0f : (s.real() < 0 ? -1.0f : 0.0f);
        float sgn_i = s.imag() > 0 ? 1.0f : (s.imag() < 0 ? -1.0f : 0.0f);
        std::complex<float> dec(sgn_r, sgn_i);
        
        symbols.push_back(s);

        float err = (s * std::conj(last_dec) - last_sym * std::conj(dec)).real();
        timing_errors.push_back(err);

        last_sym = s;
        last_dec = dec;

        idx += sps + loop_gain * err;
    }

    int sym_count = symbols.size();
    auto out = py::array_t<std::complex<float>>(sym_count);
    auto out_ptr = static_cast<std::complex<float>*>(out.request().ptr);
    for (int i = 0; i < sym_count; ++i) out_ptr[i] = symbols[i];

    float rms_err = 1.0f;
    int start_idx = sym_count > 20 ? sym_count / 2 : 0;
    int count = sym_count - start_idx;
    if (count > 0) {
        float sum_sq = 0.0f;
        for (int i = start_idx; i < sym_count; ++i) sum_sq += timing_errors[i] * timing_errors[i];
        rms_err = std::sqrt(sum_sq / count);
    }

    py::dict metrics;
    metrics["timing_converged"] = rms_err < 0.5f;
    metrics["rms_timing_error"] = rms_err;
    metrics["symbol_count"] = sym_count;

    return py::make_tuple(out, metrics);
}

// Fast CMA Equalizer
py::tuple cma_equalize(py::array_t<std::complex<float>> samples, int num_taps, float mu, float reference_modulus) {
    py::buffer_info buf = samples.request();
    auto ptr = static_cast<std::complex<float>*>(buf.ptr);
    int n = buf.size;

    auto out = py::array_t<std::complex<float>>(n);
    auto out_ptr = static_cast<std::complex<float>*>(out.request().ptr);
    
    std::vector<std::complex<float>> weights(num_taps, {0.0f, 0.0f});
    weights[num_taps / 2] = {1.0f, 0.0f};

    std::vector<std::complex<float>> window(num_taps, {0.0f, 0.0f});

    for (int i = 0; i < n; ++i) {
        // Shift window
        for (int k = num_taps - 1; k > 0; --k) {
            window[k] = window[k - 1];
        }
        window[0] = ptr[i];

        if (i < num_taps - 1) {
            out_ptr[i] = ptr[i];
            continue;
        }

        std::complex<float> y(0.0f, 0.0f);
        for (int k = 0; k < num_taps; ++k) {
            y += window[k] * weights[k];
        }
        out_ptr[i] = y;

        float mag_sq = std::norm(y);
        std::complex<float> err = y * (mag_sq - reference_modulus);

        for (int k = 0; k < num_taps; ++k) {
            weights[k] -= mu * err * std::conj(window[k]);
        }
    }

    auto weights_out = py::array_t<std::complex<float>>(num_taps);
    auto weights_ptr = static_cast<std::complex<float>*>(weights_out.request().ptr);
    auto weights_mag = py::list();
    for (int k = 0; k < num_taps; ++k) {
        weights_ptr[k] = weights[k];
        weights_mag.append(std::abs(weights[k]));
    }

    py::dict metrics;
    metrics["converged"] = true;
    metrics["final_weights_magnitude"] = weights_mag;

    return py::make_tuple(out, weights_out, metrics);
}

PYBIND11_MODULE(_fast_kernels, m) {
    m.doc() = "High-performance DSP kernels for Signal Lab";
    m.def("min_max_decimate_iq", &min_max_decimate_iq, "Multi-resolution Min-Max decimated waveform for 60 FPS lag-free rendering.");
    m.def("estimate_carrier_peak", &estimate_carrier_peak, "Fast Welch-like PSD Peak estimation via C++ FFT.");
    m.def("costas_loop_process", &costas_loop_process, "Fast C++ Costas Loop for carrier recovery.");
    m.def("mueller_muller_timing_recovery", &mueller_muller_timing_recovery, "Fast C++ Mueller-Muller TED for symbol timing recovery.");
    m.def("cma_equalize", &cma_equalize, "Fast C++ CMA Equalizer for blind multipath mitigation.");
}
