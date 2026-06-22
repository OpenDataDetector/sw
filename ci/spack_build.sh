#!/bin/bash

set -u
set -e
set -o pipefail

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}"   )" &> /dev/null && pwd   )

export SPACK_COLOR=always


function start_section() {
    local section_name="$1"
    if [ -n "${GITHUB_ACTIONS:-}" ]; then
        echo "::group::${section_name}"
    else
        echo "+ ${section_name}"
    fi
}

function end_section() {
  echo "" > /dev/null
    if [ -n "${GITHUB_ACTIONS:-}" ]; then
        echo "::endgroup::"
    fi
}


if [ -z "${SPACK_ROOT:-}" ]; then
    echo "SPACK_ROOT is not set"
    exit 1
fi

if [ -z "${COMPILER:-}" ]; then
    echo "COMPILER is not set"
    exit 1
fi

if [ -z "${CXXSTD:-}" ]; then
    echo "CXXSTD is not set"
    exit 1
fi


start_section "Setting up spack from $SPACK_ROOT"
source "$SPACK_ROOT"/share/spack/setup-env.sh
end_section


echo "Spack version: $(spack --version)"

start_section "Create environment"
spack env activate "$PWD"
end_section

start_section "List visible compilers"
if [ -n "${COMPILER_PATH:-}" ]; then
spack -e . compiler find --scope "env:$PWD" "${COMPILER_PATH:-}"
else
spack -e . compiler find --scope "env:$PWD"
fi
spack -e . compiler list
end_section

start_section "Locate OpenGL"
"$SCRIPT_DIR"/opengl.sh
end_section

start_section "Select compiler and cxxstd"
spack -e . compiler list
echo "Looking for compiler: $COMPILER"
spack -e . compiler list | grep "$COMPILER"
# Scope the compiler requirement to the language virtuals (c/cxx/fortran)
# rather than `packages:all`, which Spack warns can cause concretization
# errors. The cxxstd requirement still applies to all packages.
spack -e . config add "packages:all:require:[\"cxxstd=$CXXSTD\"]"
for _lang in c cxx fortran; do
  # Require the provider of each language virtual directly (no leading '%',
  # which is only valid in a 'packages:all' compiler requirement).
  spack -e . config add "packages:${_lang}:require:[\"$COMPILER\"]"
done
end_section

start_section "Concretize"
spack -e . concretize -Uf
spack -e . find -c
end_section

echo "+ Spack build"
args="--no-check-signature --show-log-on-error --concurrent-packages 8"
if [ -n "${FAIL_FAST:-}" ]; then
  args="$args --fail-fast"
fi
spack -e . install $args

function set_env {
  key="$1"
  value="$2"

  echo "=> ${key}=${value}"

  export "${key}=${value}"
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "${key}=${value}" >> "$GITHUB_ENV"
  fi
}

set_env TARGET_ARCH "$(spack arch --family)"
set_env TARGET_TRIPLET "${TARGET_ARCH}_${COMPILER}_cxx${CXXSTD}"
