# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.build_systems.cuda import CudaPackage

from spack.package import *


class Acts(CMakePackage, CudaPackage):
    """
    A Common Tracking Software (Acts)

    This project contains an experiment-independent set of track reconstruction
    tools. The main philosophy is to provide high-level track reconstruction
    modules that can be used for any tracking detector. The description of the
    tracking detector's geometry is optimized for efficient navigation and
    quick extrapolation of tracks. Converters for several common geometry
    description languages exist. Having a highly performant, yet largely
    customizable implementation of track reconstruction algorithms was a
    primary objective for the design of this toolset. Additionally, the
    applicability to real-life HEP experiments plays major role in the
    development process. Apart from algorithmic code, this project also
    provides an event data model for the description of track parameters and
    measurements.

    Key features of this project include: tracking geometry description which
    can be constructed from TGeo, DD4Hep, or GDML input, simple and efficient
    event data model, performant and highly flexible algorithms for track
    propagation and fitting, basic seed finding algorithms.
    """

    homepage = "https://acts.web.cern.ch/ACTS/"
    git = "https://github.com/acts-project/acts.git"
    url = "https://github.com/acts-project/acts/releases/download/v43.2.0/acts-v43.2.0.tar.gz"
    list_url = "https://github.com/acts-project/acts/releases/"
    maintainers("wdconinc", "stephenswat")

    tags = ["hep"]

    license("MPL-2.0")

    # Supported Acts versions
    version("main", branch="main")
    version("master", branch="main", deprecated=True)  # For compatibility

    version("43.2.0", sha256="d237c106a22e2682b0ec028e6d5a155fb70f4528600f037e45e249f3e69977c8")
    version("43.1.0", sha256="21b7586dcda1bb3e6982fd7e1fe949f95c9545d4e557b4ab78d2fe511c9fd185")
    version("43.0.0", sha256="c5529a421b78384af8fc503060d73c10b813b8e902368ffc7b6265af46a33a05")
    version("43.0.1", sha256="5ba2ffbd2b6fd2f91e3978ee0d1cda830f701d864f69c459a310c07461b407d9")
    version("43.0.0", sha256="c5529a421b78384af8fc503060d73c10b813b8e902368ffc7b6265af46a33a05")

    version("39.2.0", commit="94cf48783efd713f38106b18211d1c59f4e8cdec", submodules=True)
    version("39.1.0", commit="09225b0d0bba24d57a696e347e3027b39404bb75", submodules=True)
    version("39.0.0", commit="b055202e2fbdd509bc186eb4782714bc46f38f3f", submodules=True)
    version("38.2.0", commit="9cb8f4494656553fd9b85955938b79b2fac4c9b0", submodules=True)
    version("38.1.0", commit="8a20c88808f10bf4fcdfd7c6e077f23614c3ab90", submodules=True)
    version("38.0.0", commit="0a6b5155e29e3b755bf351b8a76067fff9b4214b", submodules=True)
    version("37.4.0", commit="4ae9a44f54c854599d1d753222ec36e0b5b4e9c7", submodules=True)
    version("37.3.0", commit="b3e856d4dadcda7d1a88a9b846ce5a7acd8410c4", submodules=True)
    version("37.2.0", commit="821144dc40d35b44aee0d7857a0bd1c99e4a3932", submodules=True)
    version("37.1.0", commit="fa6ad4d52e0bd09cf8c78507fcbb18e9ac2c87a3", submodules=True)
    version("37.0.1", commit="998b9c9dd42d5160c2540f8fa820505869bfdb79", submodules=True)
    version("37.0.0", commit="117feaaadc7a2336755274e0cd70ba58a047a1de", submodules=True)

    # Variants that affect the core Acts library
    variant(
        "benchmarks", default=False, description="Build the performance benchmarks", when="@0.16:"
    )
    _cxxstd_values = (conditional("20", when="@24:"),)
    _cxxstd_common = {
        "values": _cxxstd_values,
        "multi": False,
        "description": "Use the specified C++ standard when building.",
    }
    variant("cxxstd", default="17", when="@:35", **_cxxstd_common)
    variant("cxxstd", default="20", when="@36:", **_cxxstd_common)
    variant("examples", default=False, description="Build the examples")
    variant("integration_tests", default=False, description="Build the integration tests")
    variant("unit_tests", default=False, description="Build the unit tests")
    variant(
        "log_failure_threshold",
        default="MAX",
        description="Log level above which examples should auto-crash",
    )
    _scalar_values = ["float", "double"]
    variant(
        "scalar",
        default="double",
        values=_scalar_values,
        multi=False,
        sticky=True,
        description="Scalar type to use throughout Acts.",
    )

    # Variants that enable / disable Acts plugins
    variant("alignment", default=False, description="Build the alignment package")
    variant("dd4hep", default=False, description="Build the DD4hep plugin", when="+tgeo")
    variant("digitization", default=False, description="Build the geometric digitization plugin")
    variant("edm4hep", default=False, description="Build EDM4hep plugin")
    variant("podio", default=False, description="Build PODIO plugin")
    # FIXME: Can't build Exa.TrkX plugin+examples yet, missing cuGraph dep
    variant("fatras", default=False, description="Build the FAst TRAcking Simulation package")
    variant("fatras_geant4", default=False, description="Build Geant4 Fatras package")
    variant("geomodel", default=False, description="Build GeoModel plugin", when="@33:")
    variant(
        "identification", default=False, description="Build the Identification plugin", when="@:34"
    )
    variant("json", default=False, description="Build the Json plugin")
    variant("legacy", default=False, description="Build the Legacy package")
    variant("onnx", default=False, description="Build ONNX plugin")
    variant("profilecpu", default=False, description="Enable CPU profiling using gperftools")
    variant("profilemem", default=False, description="Enable memory profiling using gperftools")
    variant("tgeo", default=False, description="Build the TGeo plugin")
    variant("traccc", default=False, description="Build the Traccc plugin")

    # Variants that only affect Acts examples for now
    variant(
        "geant4", default=False, description="Build the Geant4-based examples", when="+examples"
    )
    variant(
        "hepmc3", default=False, description="Build the HepMC3-based examples", when="+examples"
    )
    variant(
        "pythia8", default=False, description="Build the Pythia8-based examples", when="+examples"
    )
    variant(
        "python",
        default=False,
        description="Build python bindings for the examples",
        when="+examples",
    )
    variant("svg", default=False, description="Build ActSVG display plugin")
    variant(
        "tbb",
        default=True,
        description="Build the examples with Threading Building Blocks library",
        when="+examples",
    )
    variant("analysis", default=False, description="Build analysis applications in the examples")

    # Build dependencies
    depends_on("c", type="build", when="+dd4hep")  # DD4hep requires C
    depends_on("cxx", type="build")
    with when("+svg"):
        depends_on("actsvg@0.4.51:")  # https://github.com/acts-project/actsvg/issues/94
    depends_on("acts-algebra-plugins @0.24:", when="+traccc")
    depends_on("boost @1.71: +filesystem +program_options +test")
    depends_on("cmake @3.14:", type="build")
    depends_on("covfie @0.10:", when="+traccc")
    depends_on("cuda @12:", when="+traccc")
    depends_on("dd4hep @1.21: +dddetectors +ddrec", when="+dd4hep")
    depends_on("dd4hep +ddg4", when="+dd4hep +geant4 +examples")
    depends_on("detray @0.75.3:", when="+traccc")
    depends_on("edm4hep @0.7:", when="+edm4hep")
    depends_on("eigen @3.4:")
    depends_on("geant4", when="+fatras_geant4")
    depends_on("geant4", when="+geant4")
    depends_on("geomodel +geomodelg4", when="+geomodel")
    depends_on("geomodel @6.8.0:", when="+geomodel")
    depends_on("git-lfs", when="@12.0.0:")
    depends_on("gperftools", when="+profilecpu")
    depends_on("gperftools", when="+profilemem")
    depends_on("hepmc3 @3.3.0:", when="+hepmc3")
    depends_on("heppdt", when="+hepmc3 @:4.0")
    depends_on("intel-tbb @2020.1:", when="+examples +tbb")
    depends_on("intel-tbb @2020.1:", when="+examples @37.3:")
    depends_on("nlohmann-json @3.10.5:", when="+json")
    depends_on("podio @0.17.4:", when="+podio")
    depends_on("pythia8", when="+pythia8")
    depends_on("python", when="+python")
    depends_on("python@3.8:", when="+python")
    depends_on("py-onnxruntime@1.12:", when="+onnx")
    depends_on("py-pybind11 @2.13.1:", when="+python")
    depends_on("py-pytest", when="+python +unit_tests")

    with when("+tgeo"):
        depends_on("root @6.28.4:")

    # ACTS imposes requirements on the C++ standard values used by ROOT
    for _cxxstd in _cxxstd_values:
        for _v in _cxxstd:
            depends_on(f"geant4 cxxstd={_v.value}", when=f"cxxstd={_v.value} +geant4")
            depends_on(f"geant4 cxxstd={_v.value}", when=f"cxxstd={_v.value} +fatras_geant4")
            depends_on(f"root cxxstd={_v.value}", when=f"cxxstd={_v.value} +tgeo")

    # When the traccc plugin is enabled, detray should match the Acts scalars
    with when("+traccc"):
        for _scalar in _scalar_values:
            depends_on(f"detray scalar={_scalar}", when=f"scalar={_scalar}")

    # ACTS enables certain options anyway based on other options
    conflicts("~svg", when="+traccc")
    conflicts("~json", when="+traccc")

    # When using C++20, disable gcc 9 and lower.
    conflicts("%gcc@:9", when="cxxstd=20")
    # See https://github.com/acts-project/acts/pull/3512
    conflicts("^boost@1.85.0")

    def cmake_args(self):
        spec = self.spec

        def cmake_variant(cmake_label, spack_variant):
            enabled = spec.satisfies("+" + spack_variant)
            return f"-DACTS_BUILD_{cmake_label}={enabled}"

        def enable_cmake_variant(cmake_label, spack_variant):
            enabled = spec.satisfies(spack_variant)
            return f"-DACTS_ENABLE_{cmake_label}={enabled}"

        def example_cmake_variant(cmake_label, spack_variant, type="BUILD"):
            enabled = spec.satisfies("+examples +" + spack_variant)
            return f"-DACTS_{type}_EXAMPLES_{cmake_label}={enabled}"

        def plugin_label(plugin_name):
            if spec.satisfies("@0.33:"):
                return "PLUGIN_" + plugin_name
            else:
                return plugin_name + "_PLUGIN"

        def plugin_cmake_variant(plugin_name, spack_variant):
            return cmake_variant(plugin_label(plugin_name), spack_variant)

        integration_tests_label = "INTEGRATIONTESTS"
        unit_tests_label = "UNITTESTS"
        legacy_plugin_label = "LEGACY_PLUGIN"
        if spec.satisfies("@:0.15"):
            integration_tests_label = "INTEGRATION_TESTS"
            unit_tests_label = "TESTS"
        if spec.satisfies("@:0.32"):
            legacy_plugin_label = "LEGACY"

        args = [
            cmake_variant("ALIGNMENT", "alignment"),
            cmake_variant("ANALYSIS_APPS", "analysis"),
            plugin_cmake_variant("AUTODIFF", "autodiff"),
            cmake_variant("BENCHMARKS", "benchmarks"),
            example_cmake_variant("BINARIES", "binaries"),
            plugin_cmake_variant("CUDA", "cuda"),
            plugin_cmake_variant("DD4HEP", "dd4hep"),
            example_cmake_variant("DD4HEP", "dd4hep"),
            plugin_cmake_variant("DIGITIZATION", "digitization"),
            plugin_cmake_variant("EDM4HEP", "edm4hep"),
            example_cmake_variant("EDM4HEP", "edm4hep"),
            cmake_variant("EXAMPLES", "examples"),
            cmake_variant("FATRAS", "fatras"),
            cmake_variant("FATRAS_GEANT4", "fatras_geant4"),
            example_cmake_variant("GEANT4", "geant4"),
            plugin_cmake_variant("GEANT4", "geant4"),
            plugin_cmake_variant("GEOMODEL", "geomodel"),
            example_cmake_variant("HEPMC3", "hepmc3"),
            plugin_cmake_variant("IDENTIFICATION", "identification"),
            cmake_variant(integration_tests_label, "integration_tests"),
            plugin_cmake_variant("JSON", "json"),
            cmake_variant(legacy_plugin_label, "legacy"),
            cmake_variant("ODD", "odd"),
            plugin_cmake_variant("ONNX", "onnx"),
            enable_cmake_variant("CPU_PROFILING", "profilecpu"),
            enable_cmake_variant("MEMORY_PROFILING", "profilemem"),
            plugin_cmake_variant("PODIO", "podio"),
            example_cmake_variant("PYTHIA8", "pythia8"),
            example_cmake_variant("PYTHON_BINDINGS", "python"),
            self.define_from_variant("ACTS_CUSTOM_SCALARTYPE", "scalar"),
            plugin_cmake_variant("ACTSVG", "svg"),
            plugin_cmake_variant("SYCL", "sycl"),
            plugin_cmake_variant("TGEO", "tgeo"),
            example_cmake_variant("TBB", "tbb", "USE"),
            plugin_cmake_variant("TRACCC", "traccc"),
            cmake_variant(unit_tests_label, "unit_tests"),
        ]

        log_failure_threshold = spec.variants["log_failure_threshold"].value
        args.append(f"-DACTS_LOG_FAILURE_THRESHOLD={log_failure_threshold}")
        if spec.satisfies("@19.4.0:"):
            args.append("-DACTS_ENABLE_LOG_FAILURE_THRESHOLD=ON")

        # Use dependencies provided by spack
        if spec.satisfies("@20.3:"):
            args.append("-DACTS_USE_SYSTEM_LIBS=ON")
            if spec.satisfies("@35.1:36.0"):
                args.append("-DACTS_USE_SYSTEM_DFELIBS=OFF")
        else:
            if spec.satisfies("+autodiff"):
                args.append("-DACTS_USE_SYSTEM_AUTODIFF=ON")

            if spec.satisfies("@19:20.2 +dd4hep"):
                args.append("-DACTS_USE_SYSTEM_ACTSDD4HEP=ON")

            if spec.satisfies("@0.33: +json"):
                args.append("-DACTS_USE_SYSTEM_NLOHMANN_JSON=ON")
            elif spec.satisfies("@0.14.0:0.32 +json"):
                args.append("-DACTS_USE_BUNDLED_NLOHMANN_JSON=OFF")

            if spec.satisfies("@18: +python"):
                args.append("-DACTS_USE_SYSTEM_PYBIND11=ON")

            if spec.satisfies("@20.1: +svg"):
                args.append("-DACTS_USE_SYSTEM_ACTSVG=ON")

            if spec.satisfies("@14: +vecmem"):
                args.append("-DACTS_USE_SYSTEM_VECMEM=ON")

        if spec.satisfies("+cuda"):
            cuda_arch = spec.variants["cuda_arch"].value
            if cuda_arch != "none":
                args.append(f"-DCUDA_FLAGS=-arch=sm_{cuda_arch[0]}")
                arch_str = ";".join(self.spec.variants["cuda_arch"].value)
                args.append(self.define("CMAKE_CUDA_ARCHITECTURES", arch_str))

        args.append(self.define_from_variant("CMAKE_CXX_STANDARD", "cxxstd"))

        return args
