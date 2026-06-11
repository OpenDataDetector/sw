# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.build_systems.cmake import CMakePackage, generator
from spack_repo.builtin.packages.dd4hep.package import Dd4hep as DD4hepBase

from spack.package import *


# Inherit everything from builtin.dd4hep, but override the source repository
class Dd4hep(DD4hepBase):
    git = "https://github.com/murnanedaniel/DD4hep.git"

    def url_for_version(self, version):
        # The builtin url_for_version assumes a numeric release version and
        # does "v%02d-%02d" % (major, minor) formatting. We pin dd4hep to a
        # git ref (...=master), whose version components are non-numeric
        # VersionStrComponents, so that formatting raises TypeError. Spack's
        # post-install SBOM hook (sbom_generate.py) calls url_for_version for
        # every spec, so the crash kills an otherwise-successful build. Guard
        # non-numeric versions and let the SBOM fall back to "NOASSERTION".
        try:
            return super().url_for_version(version)
        except (TypeError, ValueError):
            return None
