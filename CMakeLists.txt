cmake_minimum_required(VERSION 3.20)
project(signal_lab_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Optional pybind11 integration for native fast kernels
find_package(pybind11 QUIET)

if(pybind11_FOUND)
    pybind11_add_module(fast_kernels cpp/fast_kernels.cpp)
    target_include_directories(fast_kernels PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/cpp)
else()
    message(STATUS "pybind11 not found; skipping native C++ module build. Pure Python/SciPy fallbacks active.")
endif()
