import sys
import tempfile
from typing import ClassVar

import pybind11
from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class get_pybind_include:
    """Helper class to determine the pybind11 include path.

    Postpones importing pybind11 until installed.
    """

    def __init__(self, user: bool = False):
        self.user = user

    def __str__(self) -> str:
        return pybind11.get_include(self.user)


ext_modules = [
    Extension(
        "signal_lab.dsp._fast_kernels",
        ["signal_lab/dsp/fast_kernels.cpp"],
        include_dirs=[get_pybind_include(), get_pybind_include(user=True)],
        language="c++",
    ),
]


def has_flag(compiler, flagname: str) -> bool:
    """Return a boolean indicating whether a flag name is supported."""
    with tempfile.NamedTemporaryFile("w", suffix=".cpp") as f:
        f.write("int main (int argc, char **argv) { return 0; }")
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except (OSError, RuntimeError):
            return False
    return True


def cpp_flag(compiler) -> str:
    """Return the -std=c++[11/14/17] compiler flag."""
    flags = ["-std=c++17", "-std=c++14", "-std=c++11"]
    for flag in flags:
        if has_flag(compiler, flag):
            return flag
    raise RuntimeError("Unsupported compiler -- at least C++11 support is needed!")


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""

    c_opts: ClassVar[dict[str, list[str]]] = {
        "msvc": ["/EHsc"],
        "unix": [],
    }
    l_opts: ClassVar[dict[str, list[str]]] = {
        "msvc": [],
        "unix": [],
    }

    if sys.platform == "darwin":
        darwin_opts = ["-stdlib=libc++", "-mmacosx-version-min=10.7"]
        c_opts["unix"] += darwin_opts
        l_opts["unix"] += darwin_opts

    def build_extensions(self) -> None:
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        link_opts = self.l_opts.get(ct, [])
        if ct == "unix":
            opts.append(f'-DVERSION_INFO="{self.distribution.get_version()}"')
            opts.append(cpp_flag(self.compiler))
            if has_flag(self.compiler, "-fvisibility=hidden"):
                opts.append("-fvisibility=hidden")
            opts.append("-O3")
            opts.append("-ffast-math")
            opts.append("-march=native")
        elif ct == "msvc":
            opts.append(f'/DVERSION_INFO=\\"{self.distribution.get_version()}\\"')
        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts
        super().build_extensions()


setup(
    name="signal_lab_dsp",
    version="1.0.0",
    description="Fast DSP kernels for Signal Lab",
    ext_modules=ext_modules,
    setup_requires=["pybind11>=2.5.0"],
    cmdclass={"build_ext": BuildExt},
    zip_safe=False,
)
