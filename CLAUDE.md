# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository contains a Spack-based environment for building and deploying particle physics software packages. The primary focus is on ACTS (A Common Tracking Software) and related high-energy physics (HEP) packages like DD4hep, Geant4, HepMC3, Pythia8, and MadGraph.

## Architecture

### Spack Environment Management

The repository uses **Spack** as the primary package manager for managing complex HEP software dependencies. Key components:

- **spack.yaml**: Defines the complete software environment specification
- **spack.lock**: Lockfile for reproducible builds (auto-generated, gitignored)
- **spack_repo/colliderml/**: Custom Spack repository with namespace `colliderml`

### Custom Spack Packages

Located in `spack_repo/colliderml/packages/`, these override or extend built-in Spack packages:

- **acts**: Custom fork pointing to `paulgessinger/acts` with a `develop` version mapped to the `colliderml` branch
- **dd4hep**: Override pointing to `murnanedaniel/DD4hep` fork
- **lhapdfsets**: Bundle package for LHAPDF parton density function datasets
- **hepmc3**, **madgraph5amc**, **syscalc**, **edm4hep**: Additional custom package definitions

When modifying packages, ensure compatibility with the unified concretization strategy (`concretizer.unify: true`).

### Container Architecture

The repository supports both manual Dockerfiles and Spack-generated container images:

- **Dockerfile**: Static container definition (may be out of sync with spack.yaml)
- **Dockerfile.jinja2**: Template extending Spack's base container template
- Container builds use a two-stage pattern: builder stage with Spack + bare runtime stage

The Spack container template is configured via `config.template_dirs` in spack.yaml.

### Build Cache Strategy

Two OCI registries are configured as mirrors:

1. **Primary cache**: `oci://ghcr.io/opendatadetector/sw` (requires GH_OCI_USER/GH_OCI_TOKEN)
2. **ACTS cache**: `oci://ghcr.io/acts-project/spack-buildcache` (public)

Builds push to the primary cache, significantly accelerating subsequent builds.

## Common Development Commands

### Working with the Spack environment

```bash
# Activate the environment
spack env activate .

# Concretize (resolve all dependencies)
spack -e . concretize -Uf

# Install all packages
spack -e . install

# Install with logging and parallelism
spack -e . install --show-log-on-error --concurrent-packages 8

# View installed packages
spack -e . find -c

# Push to buildcache
spack -e . buildcache push --base-image <base_image> --unsigned cache
```

### CI Workflow

The GitHub Actions workflow (`.github/workflows/build.yml`) automates:

1. Environment setup with `spack/setup-spack@v2`
2. Disk cleanup via `ci/uninstall_packages.py` (removes large packages on GitHub runners)
3. Containerized build using `ci/spack_build.sh`
4. Cache push using `ci/spack_push.sh`

**Key environment variables**:
- `IMAGE`: Base Docker image (e.g., `ghcr.io/acts-project/ubuntu2404:82`)
- `COMPILER`: Compiler spec (e.g., `gcc@13.3.0`)
- `GH_OCI_USER` / `GH_OCI_TOKEN`: OCI registry credentials

The build runs inside a Docker container with mounted volumes for `/src`, `/spack`, and `/build`.

### Building Containers

```bash
# Generate Dockerfile from spack.yaml
spack -e . containerize > Dockerfile.generated

# Build container using Docker
docker build -t colliderml-sw .
```

The Jinja2 template approach is preferred: it copies the custom `spack_repo/` into the build stage.

## Key Software Packages

The environment builds:

- **ACTS** (main branch): Tracking reconstruction toolkit with plugins for DD4hep, Geant4, HepMC3, Pythia8, EDM4hep, TGeo, JSON, and Fatras
- **DD4hep**: Detector description toolkit with Geant4 and EDM4hep support
- **ROOT**: Data analysis framework (without OpenGL/X11)
- **Geant4**: Particle physics simulation (data packages excluded via `-data`)
- **Pythia8**: Event generator with HepMC3 and LHAPDF support
- **MadGraph5**: Matrix element generator with Pythia8 integration
- **FastJet**: Jet clustering
- **GeoModel**: Geometry description library

Python 3.14 with pybind11, pip, jinja2, and pyyaml is included for EDM4hep/Podio support.

## Important Patterns

### When modifying spack.yaml

1. Ensure all custom packages exist in `spack_repo/colliderml/packages/`
2. Use the `colliderml.` prefix for packages from the custom repo (e.g., `colliderml.acts`)
3. Rebuild the lockfile: `spack -e . concretize -Uf`
4. Test builds locally before CI

### When adding new custom packages

1. Create directory: `spack_repo/colliderml/packages/<package_name>/`
2. Add `package.py` inheriting from Spack's built-in package or BundlePackage
3. Reference with `colliderml.<package_name>` in spack.yaml

### CI disk space constraints

GitHub runners have limited disk. The `ci/uninstall_packages.py` script removes unnecessary packages (dotnet, Azure CLI, Chrome, etc.) before builds. If builds fail with disk errors, consider:

- Adding more packages to the removal patterns
- Reducing concurrency: `--concurrent-packages` value
- Leveraging the buildcache more aggressively
