# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.madgraph5amc.package import (
    Madgraph5amc as Madgraph5amcBase,
)

from spack.package import *


# Inherit everything from builtin.madgraph5amc, but add additional versions
class Madgraph5amc(Madgraph5amcBase):
    version(
        "3.5.9",
        sha256="1e707fcd18f5b967c3f6220b3e5538622c93472376cae6666c56d0f2c2dd4b92",
    )
