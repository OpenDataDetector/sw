# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack_repo.builtin.packages.madgraph5amc.package import (
    Madgraph5amc as Madgraph5amcBase,
)

from spack.package import *

import shutil
import os


# Inherit everything from builtin.madgraph5amc, but add additional versions
class Madgraph5amc(Madgraph5amcBase):
    def install(self, spec, prefix):
        def installdir(dirname):
            install_tree(dirname, join_path(prefix, dirname))

        def installfile(filename):
            install(filename, join_path(prefix, filename))

        for p in os.listdir(self.stage.source_path):
            if os.path.isdir(p):
                installdir(p)
            else:
                if p != "doc.tgz":
                    installfile(p)
                else:
                    mkdirp(prefix.share)
                    install(p, join_path(prefix.share, p))

        install(
            join_path("Template", "LO", "Source", ".make_opts"),
            join_path(prefix, "Template", "LO", "Source", "make_opts"),
        )

        # TODO: Fix for reproducibility, see https://github.com/spack/spack/pull/41128#issuecomment-2305777485
        if "+pythia8" in spec:
            # Overwrite Pythia8's version of `JetMatching.h` with the one from MadGraph5_aMC@NLO
            src = join_path(
                self.prefix, "Template", "NLO", "MCatNLO", "Scripts", "JetMatching.h"
            )
            dst = join_path(
                self.spec["pythia8"].prefix,
                "include",
                "Pythia8Plugins",
                "JetMatching.h",
            )
            backup = dst + ".orig"
            if not os.path.exists(backup):
                shutil.copy2(dst, backup)

            shutil.copy2(src, dst)

            with open("install-pythia8-interface", "w") as f:
                f.write(
                    f"""set pythia8_path {spec["pythia8"].prefix}
                            install mg5amc_py8_interface
                    """
                )
            mg5 = Executable(join_path(prefix, "bin", "mg5_aMC"))
            mg5("install-pythia8-interface")
