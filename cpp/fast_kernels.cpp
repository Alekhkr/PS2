// Fast C++ kernels for Signal Lab (SIMD energy detection and fast correlator)

#include <vector>
#include <complex>
#include <cmath>

#if __has_include(<pybind11/pybind11.h>)
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
namespace py = pybind11;

// Fast energy detector kernel
py::array_t<float> compute_power_profile(py::array_t<std::complex<float>> input) {
    auto buf = input.request();
    auto* ptr = static_cast<std::complex<float>*>(buf.ptr);
    size_t n = buf.size;

    auto result = py::array_t<float>(n);
    auto res_buf = result.request();
    float* res_ptr = static_cast<float*>(res_buf.ptr);

    for (size_t i = 0; i < n; ++i) {
        float r = ptr[i].real();
        float im = ptr[i].imag();
        res_ptr[i] = r * r + im * im;
    }
    return result;
}

PYBIND11_MODULE(fast_kernels, m) {
    m.doc() = "Native C++ accelerated signal analysis kernels";
    m.def("compute_power_profile", &compute_power_profile, "Fast SIMD power profile");
}
#endif
