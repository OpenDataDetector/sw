# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage
from spack_repo.builtin.packages.hepmc3.package import Hepmc3 as Hepmc3Base

from spack.package import *

class Hepmc3(Hepmc3Base):
    version("3.3.1", sha256="08240160b0f28dc3293aa4d61ce65e2d67cd597acf6faca439f2e46625f7e793")

