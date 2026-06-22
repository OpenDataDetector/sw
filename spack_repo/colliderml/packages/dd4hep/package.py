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
        # This fork is built from a git ref (e.g. "@...=master"), which has no
        # release tarball. The base implementation formats numeric version
        # components with %d and raises a TypeError on non-numeric git
        # versions (e.g. when the SBOM hook resolves a download location).
        # Use the git repository as the download location for those.
        if not str(version[0]).isdigit():
            return self.git
        return super().url_for_version(version)
