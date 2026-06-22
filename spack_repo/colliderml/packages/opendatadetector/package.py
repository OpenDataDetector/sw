# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage

from spack.package import *


class Opendatadetector(CMakePackage):
    """OpenDataDetector: detector geometry for ACTS examples and tutorials."""

    homepage = "https://gitlab.cern.ch/acts/OpenDataDetector"
    git = "https://gitlab.cern.ch/acts/OpenDataDetector.git"

    maintainers("paulgessinger")

    license("MPL-2.0")

    version("4.0.4", tag="v4.0.4")

    depends_on("cxx", type="build")
    depends_on("cmake@3.16:", type="build")
    depends_on("dd4hep")
    depends_on("root")
    depends_on("geant4")
