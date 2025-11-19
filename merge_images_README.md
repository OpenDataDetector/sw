# merge_images.py - Combine Spack OCI Layers

This script merges Spack package layers from a lockfile into a single combined OCI image without creating new layer content - only a new manifest that references existing layers.

## How it works

1. **Parses spack.lock** to extract all concrete package specs
2. **Filters packages** - removes build-only dependencies and external packages
3. **Topologically sorts** specs so dependencies come before dependents
4. **Constructs OCI layer references** for each package (e.g., `ghcr.io/acts-project/spack-buildcache:acts-41.0.0-abc123.spack`)
5. **Creates a new manifest** that references the base image + all package layers in order
6. **Uploads the manifest** to the destination registry

## Usage

```bash
uv run merge_images.py spack.lock \
  --base-image ghcr.io/acts-project/ubuntu2404:82 \
  --dest-image ghcr.io/myorg/combined:latest \
  --oci-url ghcr.io/acts-project/spack-buildcache \
  --username $GITHUB_ACTOR \
  --password $GITHUB_TOKEN
```

### Arguments

- `lockfile_path` - Path to `spack.lock` file (required)

### Options

- `--base-image, -b` - Base image to start from (required)
- `--dest-image, -d` - Destination image reference (required)
- `--oci-url, -o` - OCI URL prefix for Spack packages (default: `ghcr.io/acts-project/spack-buildcache`)
- `--username, -u` - Registry username (or set `REGISTRY_USERNAME` env var)
- `--password, -p` - Registry password (or set `REGISTRY_PASSWORD` env var)
- `--debug` - Enable debug logging to see full spec list and layer URLs

## Example with GitHub Actions

```bash
export REGISTRY_USERNAME=${{ github.actor }}
export REGISTRY_PASSWORD=${{ secrets.GITHUB_TOKEN }}

uv run merge_images.py spack.lock \
  -b ghcr.io/acts-project/ubuntu2404:82 \
  -d ghcr.io/${{ github.repository_owner }}/combined:latest \
  --debug
```

## How layers are ordered

The script uses Python's `graphlib.TopologicalSorter` to ensure dependencies come before packages that depend on them. This is critical for Docker/OCI image layer ordering.

## What gets included

- ✅ All non-external packages
- ✅ Runtime and link dependencies
- ❌ Build-only dependencies (`deptypes == ["build"]`)
- ❌ External packages (those with `external.path` set)

## Dependencies

The script uses inline dependency metadata (PEP 723) and requires:
- `opencontainers` - OCI image/manifest manipulation
- `typer` - CLI framework
- `rich` - Pretty console output
- `pydantic` - Data validation
- `requests` - HTTP library (needed by opencontainers)

Run with `uv run` to automatically install dependencies.
