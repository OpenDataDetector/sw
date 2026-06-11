#!/bin/bash

set -u
set -e
set -o pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}"   )" &> /dev/null && pwd   )

export SPACK_COLOR=always

if [ -z "${SPACK_ROOT:-}" ]; then
    echo "SPACK_ROOT is not set"
    exit 1
fi

if [ -z "${BASE_IMAGE:-}" ]; then
    echo "BASE_IMAGE is not set"
    exit 1
fi

source "$SPACK_ROOT"/share/spack/setup-env.sh

echo "+ Pushing to buildcache"
spack -e . \
  buildcache push \
  --base-image "${BASE_IMAGE}" \
  --unsigned \
  --without-build-dependencies \
  cache

  # --update-index \
  #
  # --without-build-dependencies: when a source build triggers a `go` bootstrap
  # (for the OCI push), spack pulls go + its deps in at the build host's native
  # microarch (e.g. target=zen2). Those build-only specs live in the bootstrap
  # store, not the env install DB, so a full push aborts with
  # "PackageNotInstalledError: package not installed" and (set -e) fails the
  # job. lockfile_to_docker.py already skips build-only deps, so the runtime
  # image never needs them; restricting the push to link/run deps pushes
  # exactly what the image consumes and sidesteps the bootstrap phantoms.
