# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator
from spack_repo.builtin.packages.dd4hep.package import Dd4hep as DD4hepBase

from spack.package import *

class Dd4hep(DD4hepBase):
    patch("ddsim_mt_truth.patch", when="@1.32")

if False:
    class Dd4hep(CMakePackage):
        """DD4hep is a software framework for providing a complete solution for
        full detector description (geometry, materials, visualization, readout,
        alignment, calibration, etc.) for the full experiment life cycle
        (detector concept development, detector optimization, construction,
        operation). It offers a consistent description through a single source
        of detector information for simulation, reconstruction, analysis, etc.
        It distributed under the LGPLv3 License."""

        homepage = "https://dd4hep.web.cern.ch/dd4hep/"
        url = "https://github.com/AIDASoft/DD4hep/archive/v01-12-01.tar.gz"
        git = "https://github.com/AIDASoft/DD4hep.git"

        maintainers("vvolkl", "drbenmorgan", "jmcarcell")

        tags = ["hep"]

        license("LGPL-3.0-or-later")

        version("1.32", branch="collider-ml") # pretend like this is v1.32 to make solver happy

        generator("ninja")

        # Workaround for failing build file generation in some cases
        # See https://github.com/spack/spack/issues/24232
        patch("cmake_language.patch", when="@:1.17")
        # Fix missing SimCaloHits when using the LCIO format
        patch(
            "https://github.com/AIDASoft/DD4hep/commit/2c77055fb05744a4d367123c634bcb42291df030.patch?full_index=1",
            when="@1.19:1.23",
            sha256="7bac1e08d2f83edb467da7f950b841021ecc649cc4cf21fd9043bd6d757c4e05",
        )

        # variants for subpackages
        variant("ddcad", default=True, description="Enable CAD interface based on Assimp")
        variant("ddg4", default=True, description="Enable the simulation part based on Geant4")
        variant("ddrec", default=True, description="Build DDRec subpackage.")
        variant("dddetectors", default=True, description="Build DDDetectors subpackage.")
        variant("ddcond", default=True, description="Build DDCond subpackage.")
        variant("ddalign", default=True, description="Build DDAlign subpackage.")
        variant("dddigi", default=True, description="Build DDDigi subpackage.")
        variant("ddeve", default=True, description="Build DDEve subpackage.")
        variant("utilityapps", default=True, description="Build UtilityApps subpackage.")

        # variants for other build options
        variant("doc", default=False, description="Build documentation")
        variant("xercesc", default=False, description="Enable 'Detector Builders' based on XercesC")
        variant("hepmc3", default=False, description="Enable build with hepmc3")
        variant(
            "hepmc3-gz",
            default=False,
            description="Enable build with compressed hepmc3",
            when="@1.26: +hepmc3",
        )
        variant("lcio", default=False, description="Enable build with lcio")
        variant("edm4hep", default=True, description="Enable build with edm4hep")
        variant("geant4units", default=False, description="Use geant4 units throughout")
        variant("tbb", default=False, description="Enable build with tbb")
        variant(
            "debug",
            default=False,
            description="Enable debug build flag - adds extra info in"
            " some places in addtion to the debug build type",
        )

        _cxxstd_values = ("14", "17", "20")
        variant(
            "cxxstd",
            default="20",
            values=_cxxstd_values,
            multi=False,
            description="Use the specified C++ standard when building.",
        )

        depends_on("c", type="build")
        depends_on("cxx", type="build")

        depends_on("cmake @3.12:", type="build")
        depends_on("cmake @3.14:", type="build", when="@1.26:")

        for _std in _cxxstd_values:
            for _pkg in ["boost", "root"]:
                depends_on(f"{_pkg} cxxstd={_std}", when=f"cxxstd={_std}")

        depends_on("boost @1.49:")
        depends_on("boost +system +filesystem", when="%gcc@:7")
        depends_on("root @6.08: +gdml +math +python")
        depends_on("root @6.12.2: +root7", when="@1.26:")  # DDCoreGraphics needs ROOT::ROOTHistDraw

        with when("+ddeve"):
            depends_on("root @6.08: +geom +opengl +x")
            depends_on("root @:6.27", when="@:1.23")
            conflicts("^root ~webgui", when="^root@6.28:")
            # For DD4hep >= 1.24, DDEve_Interface needs ROOT::ROOTGeomViewer only if ROOT >= 6.27
            requires("^root +root7 +webgui", when="@1.24: ^root @6.27:")
        depends_on("root @6.08: +gdml +geom +math +python +x +opengl", when="+utilityapps")

        with when("+ddg4"):
            depends_on("boost +iostreams")
            depends_on("geant4@10.2.2:")
            for _std in _cxxstd_values:
                depends_on(f"geant4 cxxstd={_std}", when=f"cxxstd={_std}")

        depends_on("imagemagick", when="+doc")
        depends_on("xerces-c", when="+xercesc")
        depends_on("assimp@5.0.2:", when="+ddcad")
        depends_on("hepmc3", when="+hepmc3")
        depends_on("hepmc3@3.2.6:", when="+hepmc3-gz")
        depends_on("bzip2", when="+hepmc3-gz")
        depends_on("xz", when="+hepmc3-gz")
        depends_on("zlib-api", when="+hepmc3-gz")
        depends_on("tbb", when="+tbb")
        depends_on("intel-tbb@:2020.3", when="+tbb @:1.23")
        depends_on("lcio", when="+lcio")
        depends_on("py-pytest", type=("build", "test"))
        with when("+edm4hep"):
            # Packages with cxxstd: note they only support 17 and onward
            for _std in ["17", "20"]:
                for _pkg in ["edm4hep", "podio"]:
                    depends_on(f"{_pkg} cxxstd={_std}", when=f"cxxstd={_std}")

            # Specific version requirements
            depends_on("edm4hep@0.10.5:", when="@1.31:")
            depends_on("podio@:0.16.03", when="@:1.23")
            depends_on("podio@:0", when="@:1.29")
            depends_on("podio@0.16:", when="@1.24:")
            depends_on("podio@0.16.3:", when="@1.26:")
            depends_on("podio@0.16.7:", when="@1.31:")

        extends("python")

        # See https://github.com/AIDASoft/DD4hep/pull/771 and https://github.com/AIDASoft/DD4hep/pull/876
        conflicts(
            "^cmake@3.16:3.17.2",
            when="@:1.18",
            msg="cmake version with buggy FindPython breaks dd4hep cmake config",
        )
        conflicts("~ddrec+dddetectors", msg="Need to enable +ddrec to build +dddetectors.")

        # See https://github.com/AIDASoft/DD4hep/issues/1210
        conflicts("^root@6.31.1:", when="@:1.27")

        @property
        def libs(self):
            # We need to override libs here, because we don't build a libdd4hep so
            # the default discovery fails. All libraries that are built by DD4hep
            # start with libDD
            return find_libraries("libDD*", root=self.prefix, shared=True, recursive=True)

        def cmake_args(self):
            spec = self.spec
            args = [
                self.define_from_variant("BUILD_DOCS", "doc"),
                self.define_from_variant("DD4HEP_USE_EDM4HEP", "edm4hep"),
                self.define_from_variant("DD4HEP_USE_XERCESC", "xercesc"),
                self.define_from_variant("DD4HEP_USE_TBB", "tbb"),
                self.define_from_variant("DD4HEP_USE_GEANT4", "ddg4"),
                self.define_from_variant("DD4HEP_USE_LCIO", "lcio"),
                self.define_from_variant("DD4HEP_USE_HEPMC3", "hepmc3"),
                self.define_from_variant("DD4HEP_USE_GEANT4_UNITS", "geant4units"),
                self.define_from_variant("DD4HEP_BUILD_DEBUG", "debug"),
                self.define_from_variant("CMAKE_CXX_STANDARD", "cxxstd"),
                # DD4hep@1.26: with hepmc3@3.2.6: allows compressed hepmc3 files
                self.define(
                    "DD4HEP_HEPMC3_COMPRESSION_SUPPORT", self.spec.satisfies("@1.26: ^hepmc3@3.2.6:")
                ),
                # Downloads assimp from github and builds it on the fly.
                # However, with spack it is preferrable to have a proper external
                # dependency, so we disable it.
                self.define("DD4HEP_LOAD_ASSIMP", False),
                self.define("BUILD_TESTING", self.run_tests),
                self.define("BOOST_ROOT", spec["boost"].prefix),
                self.define("Boost_NO_BOOST_CMAKE", True),
            ]

            packages = [
                "DDG4",
                "DDCond",
                "DDCAD",
                "DDRec",
                "DDDetectors",
                "DDAlign",
                "DDDigi",
                "DDEve",
                "UtilityApps",
            ]
            enabled_packages = [p for p in packages if self.spec.variants[p.lower()].value]
            args.append(self.define("DD4HEP_BUILD_PACKAGES", " ".join(enabled_packages)))
            return args

        def setup_run_environment(self, env: EnvironmentModifications) -> None:
            # used p.ex. in ddsim to find DDDetectors dir
            env.set("DD4hepINSTALL", self.prefix)
            env.set("DD4HEP", self.prefix.examples)
            env.set("DD4hep_DIR", self.prefix)
            env.set("DD4hep_ROOT", self.prefix)
            if len(self.libs.directories) > 0:
                env.prepend_path("LD_LIBRARY_PATH", self.libs.directories[0])

        def url_for_version(self, version):
            # dd4hep releases are dashes and padded with a leading zero
            # the patch version is omitted when 0
            # so for example v01-12-01, v01-12 ...
            base_url = self.url.rsplit("/", 1)[0]
            if len(version) == 1:
                major = version[0]
                minor, patch = 0, 0
            elif len(version) == 2:
                major, minor = version
                patch = 0
            else:
                major, minor, patch = version
            # By now the data is normalized enough to handle it easily depending
            # on the value of the patch version
            if patch == 0:
                version_str = "v%02d-%02d.tar.gz" % (major, minor)
            else:
                version_str = "v%02d-%02d-%02d.tar.gz" % (major, minor, patch)

            return base_url + "/" + version_str

        # dd4hep tests need to run after install step:
        # disable the usual check
        def check(self):
            pass

        # instead add custom check step that runs after installation
        @run_after("install")
        def build_test(self):
            with working_dir(self.build_directory):
                if self.run_tests:
                    ninja("test")
