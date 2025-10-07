# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator
from spack_repo.builtin.packages.dd4hep.package import Dd4hep as DD4hepBase

from spack.package import *


# Inherit everything from builtin.dd4hep, but override the mt patch we need
class Dd4hep(DD4hepBase):
    git = "https://github.com/murnanedaniel/DD4hep.git"

    version("develop", commit="a3fdbc4302494ee6dad3e3da460ec42b2b61c99f")

    # patch("xfull_truth_particle_handler.patch", when="@1.32")
