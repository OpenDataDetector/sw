# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator
from spack_repo.builtin.packages.dd4hep.package import Dd4hep as DD4hepBase

from spack.package import *

# Inherit everything from builtin.dd4hep, but override the mt patch we need
class Dd4hep(DD4hepBase):
    patch("ddsim_mt_truth.patch", when="@1.32")

