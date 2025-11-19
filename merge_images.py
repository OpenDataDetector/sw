#!/usr/bin/env python3

# /// script
# requires-python = ">= 3.10"
# dependencies = [
#   "opencontainers",
#   "typer",
#   "rich",
#   "pydantic",
#   "requests"
# ]
# ///

import json
import hashlib
from typing import Tuple, List, Any, Dict, Annotated
from pathlib import Path
from graphlib import TopologicalSorter
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

import typer
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
)
from pydantic import BaseModel

from opencontainers.distribution.reggie import (
    NewClient,
    WithUsernamePassword,
    WithDefaultName,
    WithDebug,
    WithName,
    WithReference,
    WithDigest,
)
from opencontainers.image.v1 import Image as OciConfig, Manifest as OciManifest

console = Console()

# Cache lock for thread safety
_cache_lock = threading.Lock()

# Get cache directory using typer
APP_NAME = "merge-images"
CACHE_DIR = Path.home() / ".cache" / APP_NAME


def get_cache_path(registry_url: str, repo: str, ref: str) -> Path:
    """Get the cache file path for a given manifest."""
    # Create a unique filename from registry, repo, and ref
    cache_key = f"{registry_url}_{repo}_{ref}".replace("/", "_").replace(":", "_")
    # Hash to keep filename reasonable length
    cache_hash = hashlib.sha256(cache_key.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{cache_hash}.json"


def load_from_cache(registry_url: str, repo: str, ref: str) -> Tuple[dict, dict] | None:
    """Load manifest and config from disk cache."""
    cache_file = get_cache_path(registry_url, repo, ref)
    if cache_file.exists():
        try:
            with cache_file.open("r") as f:
                data = json.load(f)
                return data["manifest"], data["config"]
        except Exception:
            # If cache is corrupted, ignore it
            return None
    return None


def save_to_cache(
    registry_url: str, repo: str, ref: str, manifest: dict, config: dict
) -> None:
    """Save manifest and config to disk cache."""
    cache_file = get_cache_path(registry_url, repo, ref)
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    with _cache_lock:
        with cache_file.open("w") as f:
            json.dump({"manifest": manifest, "config": config}, f)


# ----------------- Spec model for Spack packages -----------------


class Spec(BaseModel):
    """Represents a Spack package spec from the lockfile"""

    name: str
    version: str
    hash: str

    class Dependency(BaseModel):
        name: str
        hash: str

        class Parameters(BaseModel):
            deptypes: list[str]

        parameters: Parameters

        @property
        def is_build_only(self) -> bool:
            return self.parameters.deptypes == ["build"]

    dependencies: list[Dependency] | None = None

    class External(BaseModel):
        path: str

    external: External | None = None

    @property
    def is_external(self) -> bool:
        return self.external is not None

    @property
    def full_name(self) -> str:
        return f"{self.name}-{self.version}-{self.hash}"

    def full_url(self, oci_url: str) -> str:
        """Generate OCI layer reference for this spec.

        OCI tags don't allow certain characters like '=', so we sanitize them.
        Spack replaces '=' with '_' in OCI tags.
        """
        # Sanitize the tag to be OCI-compliant
        tag = f"{self.full_name}.spack"
        # Replace = with _ (Spack convention for git versions)
        tag = tag.replace("=", "_")
        return f"{oci_url}:{tag}"


# ----------------- Lockfile parsing and ordering -----------------


def parse_lockfile(lockfile_path: Path) -> Dict[str, Spec]:
    """Parse spack.lock and return dict of specs by hash"""
    with lockfile_path.open("r") as f:
        lockfile = json.load(f)

    concrete_specs = {
        h: Spec.model_validate(v) for h, v in lockfile["concrete_specs"].items()
    }

    return concrete_specs


def topological_sort_specs(specs: Dict[str, Spec]) -> List[Spec]:
    """
    Topologically sort specs so dependencies come before dependents.
    Filters out build-only dependencies and external packages.
    """
    # Build dependency graph
    graph: Dict[str, set[str]] = {}

    # Track which specs should be included (not build-only, not external)
    included_specs: set[str] = set()

    for spec_hash, spec in specs.items():
        if spec.is_external:
            continue

        included_specs.add(spec_hash)
        graph[spec_hash] = set()

        if spec.dependencies:
            for dep in spec.dependencies:
                dep_spec = specs.get(dep.hash)
                if dep_spec and not dep.is_build_only and not dep_spec.is_external:
                    graph[spec_hash].add(dep.hash)
                    # Ensure dependency is in included_specs
                    included_specs.add(dep.hash)
                    # Ensure dependency has an entry in graph
                    if dep.hash not in graph:
                        graph[dep.hash] = set()

    # Topological sort using graphlib
    sorter = TopologicalSorter(graph)
    sorted_hashes = list(sorter.static_order())

    # Convert back to Spec objects, maintaining order
    sorted_specs = [specs[h] for h in sorted_hashes if h in included_specs]

    return sorted_specs


def parse_oci_url(full_url: str) -> Tuple[str, str, str]:
    """
    Parse an OCI URL into (registry_url, repo, tag).

    Examples:
        "ghcr.io/acts-project/spack-buildcache:acts-1.0-abc.spack"
        -> ("https://ghcr.io", "acts-project/spack-buildcache", "acts-1.0-abc.spack")

        "oci://ghcr.io/acts-project/spack-buildcache:tag"
        -> ("https://ghcr.io", "acts-project/spack-buildcache", "tag")
    """
    # Remove oci:// prefix if present
    if full_url.startswith("oci://"):
        full_url = full_url[6:]

    # Split on first colon to separate image reference from tag
    if ":" in full_url:
        image_ref, tag = full_url.rsplit(":", 1)
    else:
        raise ValueError(f"OCI URL must include a tag: {full_url}")

    # Parse registry and repo
    parts = image_ref.split("/", 1)
    if len(parts) == 1:
        # No registry specified, assume docker.io
        registry = "https://registry-1.docker.io"
        repo = parts[0]
    else:
        registry_host = parts[0]
        repo = parts[1]

        # Convert registry host to full URL
        if registry_host == "docker.io":
            registry = "https://registry-1.docker.io"
        else:
            registry = f"https://{registry_host}"

    return registry, repo, tag


# ----------------- small helpers -----------------


def sha256_digest(content: bytes) -> str:
    h = hashlib.sha256()
    h.update(content)
    return f"sha256:{h.hexdigest()}"


def get_manifest_and_config(
    client, repo: str, ref: str, registry_url: str = "", debug: bool = False
) -> Tuple[dict, dict]:
    """Fetch manifest and config JSON for repo:ref. Uses persistent disk cache if available."""

    # Check disk cache first
    cached = load_from_cache(registry_url, repo, ref)
    if cached is not None:
        if debug:
            console.print(f"  [dim]Cache hit: {repo}:{ref}[/dim]")
        return cached

    if debug:
        console.print(f"  [dim]Fetching manifest: {repo}:{ref}[/dim]")

    # GET /v2/<name>/manifests/<reference>
    # Accept both single manifests and manifest lists/indexes
    accept_types = ", ".join(
        [
            "application/vnd.oci.image.manifest.v1+json",
            "application/vnd.oci.image.index.v1+json",
            "application/vnd.docker.distribution.manifest.v2+json",
            "application/vnd.docker.distribution.manifest.list.v2+json",
        ]
    )
    req = client.NewRequest(
        "GET", "/v2/<name>/manifests/<reference>", WithName(repo), WithReference(ref)
    ).SetHeader("Accept", accept_types)

    try:
        resp = client.Do(req)
        resp.raise_for_status()
    except Exception as e:
        console.print(f"[red]Error fetching manifest for {repo}:{ref}[/red]")
        console.print(f"[red]Error: {e}[/red]")
        raise

    manifest = resp.json()

    # Check if this is a manifest list/index
    media_type = manifest.get("mediaType", "")
    if media_type in [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
    ]:
        if debug:
            console.print(f"  [dim]Got manifest index, selecting platform...[/dim]")

        # Select the first linux/amd64 manifest (or just the first one)
        manifests_list = manifest.get("manifests", [])
        if not manifests_list:
            raise ValueError(f"Manifest index for {repo}:{ref} has no manifests")

        # Try to find linux/amd64
        selected_manifest = None
        for m in manifests_list:
            platform = m.get("platform", {})
            if (
                platform.get("os") == "linux"
                and platform.get("architecture") == "amd64"
            ):
                selected_manifest = m
                break

        # Fallback to first manifest
        if not selected_manifest:
            selected_manifest = manifests_list[0]

        # Fetch the actual manifest by digest
        digest = selected_manifest["digest"]
        if debug:
            console.print(f"  [dim]Fetching platform manifest: {digest}[/dim]")

        req = client.NewRequest(
            "GET",
            "/v2/<name>/manifests/<reference>",
            WithName(repo),
            WithReference(digest),
        ).SetHeader("Accept", accept_types)

        resp = client.Do(req)
        resp.raise_for_status()
        manifest = resp.json()

    cfg_desc = manifest["config"]

    # GET /v2/<name>/blobs/<digest>
    req = client.NewRequest(
        "GET",
        "/v2/<name>/blobs/<digest>",
        WithName(repo),
        WithDigest(cfg_desc["digest"]),
    )
    resp = client.Do(req)
    resp.raise_for_status()
    config = resp.json()

    # Save to disk cache
    save_to_cache(registry_url, repo, ref, manifest, config)

    return manifest, config


def upload_blob(client, repo: str, content: bytes) -> Tuple[str, int]:
    """Upload a blob (config) and return (digest, size). Uses simple 2-step upload."""
    digest = sha256_digest(content)
    size = len(content)

    # Start upload session: POST /v2/<name>/blobs/uploads/
    req = client.NewRequest("POST", "/v2/<name>/blobs/uploads/", WithName(repo))
    resp = client.Do(req)
    resp.raise_for_status()
    upload_location = resp.GetRelativeLocation()  # /v2/..../blobs/uploads/<session>

    # Finish upload in one PUT:
    # PUT <upload_location>?digest=sha256:...
    req = (
        client.NewRequest("PUT", upload_location, WithName(repo))
        .SetQueryParam("digest", digest)
        .SetHeader("Content-Length", str(size))
        .SetHeader("Content-Type", "application/octet-stream")
        .SetBody(content)
    )
    resp = client.Do(req)
    resp.raise_for_status()

    return digest, size


# ----------------- main merging logic -----------------


def merge_images(
    registry_url: str,
    username: str,
    password: str,
    src_images: List[Tuple[str, str]],  # [(repo, tag), ...] in precedence order
    dest_repo: str,
    dest_tag: str,
    debug: bool = False,
    max_workers: int = 10,
):
    """
    Create a new image dest_repo:dest_tag by concatenating the layers and
    diff_ids from src_images (in order). No new layer blobs are created.
    """

    # 1. Make a registry client
    if debug:
        console.print(f"[bold]Connecting to registry:[/bold] {registry_url}")
        console.print(
            f"[bold]Username:[/bold] {username if username else '[dim]<empty>[/dim]'}"
        )
        console.print(
            f"[bold]Password:[/bold] {'***' if password else '[dim]<empty>[/dim]'}"
        )

    client = NewClient(
        registry_url,
        WithUsernamePassword(username, password),
        WithDebug(debug),
    )

    # 2. Fetch manifests + configs in parallel
    manifests = []
    configs = []

    def fetch_one(repo: str, tag: str) -> Tuple[dict, dict]:
        return get_manifest_and_config(
            client, repo, tag, registry_url=registry_url, debug=debug
        )

    if debug:
        console.print(
            f"[bold]Fetching {len(src_images)} manifests in parallel...[/bold]"
        )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching manifests", total=len(src_images))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all fetch tasks
            future_to_index = {
                executor.submit(fetch_one, repo, tag): i
                for i, (repo, tag) in enumerate(src_images)
            }

            # Collect results in order
            results = [None] * len(src_images)
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                    progress.advance(task)
                except Exception as e:
                    repo, tag = src_images[idx]
                    console.print(f"[red]Failed to fetch {repo}:{tag}: {e}[/red]")
                    raise

            # Separate manifests and configs
            for manifest, config in results:
                manifests.append(manifest)
                configs.append(config)

    # 3. Build new config by combining all diff_ids and history
    # Start with the first config as base
    new_config = configs[0].copy()

    all_diff_ids = []
    all_history = []

    for cfg_json in configs:
        # rootfs.diff_ids is a list of uncompressed layer digests
        rootfs = cfg_json.get("rootfs", {})
        all_diff_ids.extend(rootfs.get("diff_ids", []))

        history = cfg_json.get("history", [])
        if history:
            all_history.extend(history)

    # Update the config with combined diff_ids and history
    new_config["rootfs"]["diff_ids"] = all_diff_ids
    new_config["history"] = all_history

    new_config_bytes = json.dumps(new_config).encode("utf-8")

    # 4. Build new manifest with concatenated layers
    all_layers = []
    media_type_manifest = "application/vnd.oci.image.manifest.v1+json"
    media_type_config = "application/vnd.oci.image.config.v1+json"

    for m_json in manifests:
        # Extract layers from each manifest
        layers = m_json.get("layers", [])
        all_layers.extend(layers)

    # Create new manifest structure
    new_manifest = {
        "schemaVersion": 2,
        "mediaType": media_type_manifest,
        "layers": all_layers,
    }

    # 5. Upload new config blob to dest_repo
    cfg_digest, cfg_size = upload_blob(client, dest_repo, new_config_bytes)

    # Fill in config descriptor
    new_manifest["config"] = {
        "mediaType": media_type_config,
        "size": cfg_size,
        "digest": cfg_digest,
    }

    # Convert to bytes for upload
    manifest_bytes = json.dumps(new_manifest).encode("utf-8")

    # 6. Upload manifest (PUT /v2/<name>/manifests/<reference>)
    req = (
        client.NewRequest(
            "PUT",
            "/v2/<name>/manifests/<reference>",
            WithName(dest_repo),
            WithReference(dest_tag),
        )
        .SetHeader("Content-Type", media_type_manifest)
        .SetBody(manifest_bytes)
    )
    resp = client.Do(req)
    resp.raise_for_status()

    console.print(
        f"[green]✓[/green] Created image {dest_repo}:{dest_tag} using existing layer blobs."
    )

    # Print manifest summary
    if debug:
        console.print(f"\n[bold]Final manifest:[/bold]")
        console.print(f"  Schema version: {new_manifest['schemaVersion']}")
        console.print(f"  Media type: {new_manifest['mediaType']}")
        console.print(f"  Config digest: {new_manifest['config']['digest'][:19]}...")
        console.print(f"  Config size: {new_manifest['config']['size']} bytes")
        console.print(f"  Total layers: {len(new_manifest['layers'])}")
        console.print(f"\n[bold]Layer digests:[/bold]")
        for i, layer in enumerate(new_manifest["layers"][:5], 1):  # Show first 5
            console.print(
                f"    {i}. {layer['digest'][:19]}... ({layer.get('size', 0)} bytes)"
            )
        if len(new_manifest["layers"]) > 5:
            console.print(f"    ... and {len(new_manifest['layers']) - 5} more layers")


def merge_spack_layers(
    lockfile_path: Path,
    base_image: str,
    oci_url: str,
    dest_image: str,
    username: str,
    password: str,
    debug: bool = False,
    max_workers: int = 10,
    flatten: bool = False,
) -> None:
    """
    Merge Spack package layers from a lockfile into a single combined image.

    Args:
        lockfile_path: Path to spack.lock
        base_image: Base image to start from (e.g., "ubuntu:24.04")
        oci_url: OCI URL prefix for Spack packages (e.g., "ghcr.io/acts-project/spack-buildcache")
        dest_image: Destination image reference (e.g., "ghcr.io/myorg/combined:latest")
        username: Registry username
        password: Registry password
        debug: Enable debug logging
    """
    console.print(f"[bold]Parsing lockfile:[/bold] {lockfile_path}")

    # 1. Parse lockfile
    with lockfile_path.open("r") as f:
        lockfile = json.load(f)

    specs = parse_lockfile(lockfile_path)
    console.print(f"Found {len(specs)} total specs")

    # 2. Topologically sort and filter (or just use roots if flattening)
    if flatten:
        # Only include root specs to reduce layer count
        root_hashes = [root["hash"] for root in lockfile.get("roots", [])]
        sorted_specs = [
            specs[h] for h in root_hashes if h in specs and not specs[h].is_external
        ]
        console.print(f"Flatten mode: including only {len(sorted_specs)} root specs")
    else:
        sorted_specs = topological_sort_specs(specs)
        console.print(
            f"Including {len(sorted_specs)} specs (after filtering build-only and externals)"
        )

    if debug:
        console.print("\n[bold]Spec order (dependencies first):[/bold]")
        for i, spec in enumerate(sorted_specs, 1):
            console.print(f"  {i:3d}. {spec.name}@{spec.version} ({spec.hash[:7]})")
        console.print()

    # 3. Parse base image and dest image URLs
    base_registry, base_repo, base_tag = parse_oci_url(base_image)
    dest_registry, dest_repo, dest_tag = parse_oci_url(dest_image)
    oci_registry, _, _ = parse_oci_url(f"{oci_url}:dummy")

    if debug:
        console.print(f"\n[bold]Parsed URLs:[/bold]")
        console.print(f"  Base image:  {base_registry} / {base_repo}:{base_tag}")
        console.print(f"  OCI packages: {oci_registry}")
        console.print(f"  Destination: {dest_registry} / {dest_repo}:{dest_tag}")

    # Verify all registries are the same
    # OCI manifests reference layers by digest only, so all layers must exist in the destination registry
    registries = {base_registry, oci_registry, dest_registry}
    if len(registries) > 1:
        console.print(f"\n[red bold]Error: Multiple registries detected[/red bold]")
        console.print(f"  Base image:     {base_registry}")
        console.print(f"  OCI packages:   {oci_registry}")
        console.print(f"  Destination:    {dest_registry}")
        console.print()
        console.print("[yellow]OCI manifests reference layers by digest only.[/yellow]")
        console.print(
            "[yellow]All layer blobs must exist in the destination registry.[/yellow]"
        )
        console.print()
        console.print("Options to fix this:")
        console.print("  1. Use the same registry for all images")
        console.print(f"  2. Copy the base image to {dest_registry} first")
        console.print(
            "  3. Ensure all Spack packages are in the same registry as the base image"
        )
        raise ValueError(
            f"Registry mismatch: base={base_registry}, packages={oci_registry}, dest={dest_registry}"
        )

    registry_url = base_registry

    # 4. Build src_images list: [base_image] + [spec layers]
    src_images: List[Tuple[str, str]] = [(base_repo, base_tag)]

    console.print(f"\n[bold]Building layer list:[/bold]")
    console.print(f"  Base: {base_image}")

    # Parse spec layer URLs
    for spec in sorted_specs:
        spec_url = spec.full_url(oci_url)
        _, spec_repo, spec_tag = parse_oci_url(spec_url)
        src_images.append((spec_repo, spec_tag))

        if debug:
            console.print(f"  + {spec.name}@{spec.version} -> {spec_url}")

    console.print(f"\n[bold]Total layers: {len(src_images)}[/bold]")

    # 5. Call merge_images
    console.print(f"\n[bold]Merging layers into {dest_image}...[/bold]")

    merge_images(
        registry_url=registry_url,
        username=username,
        password=password,
        src_images=src_images,
        dest_repo=dest_repo,
        dest_tag=dest_tag,
        debug=debug,
        max_workers=max_workers,
    )

    console.print(f"\n[green bold]✓ Successfully created combined image![/green bold]")
    console.print(f"  Image: {dest_image}")
    console.print(f"  Layers: {len(src_images)}")


# ----------------- CLI -----------------

app = typer.Typer()


@app.command()
def verify(
    image: Annotated[
        str,
        typer.Argument(
            help="Image to verify (e.g., 'ghcr.io/opendatadetector/sw:combined')"
        ),
    ],
    username: Annotated[
        str,
        typer.Option(
            "--username",
            "-u",
            help="Registry username (or set REGISTRY_USERNAME env var)",
            envvar="REGISTRY_USERNAME",
        ),
    ] = "",
    password: Annotated[
        str,
        typer.Option(
            "--password",
            "-p",
            help="Registry password (or set REGISTRY_PASSWORD env var)",
            envvar="REGISTRY_PASSWORD",
        ),
    ] = "",
):
    """
    Verify that an image manifest is valid and all layers exist in the registry.
    """
    console.print(f"[bold]Verifying image:[/bold] {image}")

    # Parse image URL
    registry_url, repo, tag = parse_oci_url(image)

    # Create client
    client = NewClient(
        registry_url,
        WithUsernamePassword(username, password),
        WithDebug(False),
    )

    # Fetch manifest
    console.print(f"Fetching manifest...")
    manifest, config = get_manifest_and_config(
        client, repo, tag, registry_url=registry_url, debug=False
    )

    console.print(f"[green]✓[/green] Manifest fetched successfully")
    console.print(f"  Schema version: {manifest.get('schemaVersion')}")
    console.print(f"  Media type: {manifest.get('mediaType')}")
    console.print(
        f"  Config digest: {manifest.get('config', {}).get('digest', 'N/A')[:27]}..."
    )
    console.print(f"  Total layers: {len(manifest.get('layers', []))}")

    # Check if layers exist
    layers = manifest.get("layers", [])
    console.print(f"\n[bold]Verifying {len(layers)} layers exist in registry...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Checking layers", total=len(layers))

        missing_layers = []
        for i, layer in enumerate(layers):
            digest = layer.get("digest")

            # HEAD request to check if blob exists
            req = client.NewRequest(
                "HEAD",
                "/v2/<name>/blobs/<digest>",
                WithName(repo),
                WithDigest(digest),
            )

            try:
                resp = client.Do(req)
                resp.raise_for_status()
                progress.advance(task)
            except Exception as e:
                missing_layers.append((i, digest, str(e)))
                progress.advance(task)

    if missing_layers:
        console.print(
            f"\n[red bold]✗ {len(missing_layers)} layer(s) missing from registry:[/red bold]"
        )
        for i, digest, error in missing_layers[:10]:  # Show first 10
            console.print(f"  {i+1}. {digest[:27]}... - {error}")
        if len(missing_layers) > 10:
            console.print(f"  ... and {len(missing_layers) - 10} more")
        raise typer.Exit(1)
    else:
        console.print(f"\n[green bold]✓ All layers verified![/green bold]")
        console.print(f"  Image is valid and can be pulled from {registry_url}")


@app.command()
def merge(
    lockfile_path: Annotated[
        Path,
        typer.Argument(
            help="Path to spack.lock file",
            exists=True,
            dir_okay=False,
            file_okay=True,
        ),
    ],
    base_image: Annotated[
        str,
        typer.Option(
            "--base-image",
            "-b",
            help="Base image (e.g., 'ghcr.io/acts-project/ubuntu2404:82')",
        ),
    ],
    dest_image: Annotated[
        str,
        typer.Option(
            "--dest-image",
            "-d",
            help="Destination image reference (e.g., 'ghcr.io/myorg/combined:latest')",
        ),
    ],
    oci_url: Annotated[
        str,
        typer.Option(
            "--oci-url",
            "-o",
            help="OCI URL prefix for Spack packages",
        ),
    ] = "ghcr.io/opendatadetector/sw",
    username: Annotated[
        str,
        typer.Option(
            "--username",
            "-u",
            help="Registry username (or set REGISTRY_USERNAME env var)",
            envvar="REGISTRY_USERNAME",
        ),
    ] = "",
    password: Annotated[
        str,
        typer.Option(
            "--password",
            "-p",
            help="Registry password (or set REGISTRY_PASSWORD env var)",
            envvar="REGISTRY_PASSWORD",
        ),
    ] = "",
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging"),
    ] = False,
    max_workers: Annotated[
        int,
        typer.Option(
            "--max-workers",
            "-w",
            help="Maximum number of parallel workers for fetching manifests",
        ),
    ] = 10,
    clear_cache: Annotated[
        bool,
        typer.Option("--clear-cache", help="Clear the manifest cache before running"),
    ] = False,
    flatten: Annotated[
        bool,
        typer.Option(
            "--flatten",
            help="Only include root specs (reduces layer count, similar to Dockerfile flatten mode)",
        ),
    ] = False,
):
    """
    Merge Spack package layers from a lockfile into a combined OCI image.

    This tool reads a spack.lock file, topologically sorts all package specs
    (filtering out build-only and external packages), and creates a new OCI
    image manifest that references all package layers without creating new
    layer content.

    Example:

        python merge_images.py spack.lock \\
            --base-image ghcr.io/acts-project/ubuntu2404:82 \\
            --dest-image ghcr.io/myorg/combined:latest \\
            --oci-url ghcr.io/acts-project/spack-buildcache \\
            --username $GITHUB_ACTOR \\
            --password $GITHUB_TOKEN
    """
    if not lockfile_path.exists():
        console.print(f"[red]Error:[/red] Lockfile {lockfile_path} does not exist")
        raise typer.Exit(1)

    # Clear cache if requested
    if clear_cache:
        if CACHE_DIR.exists():
            cache_files = list(CACHE_DIR.glob("*.json"))
            for f in cache_files:
                f.unlink()
            console.print(
                f"[green]✓[/green] Cleared {len(cache_files)} cached manifests"
            )
        else:
            console.print(
                "[yellow]Cache directory does not exist, nothing to clear[/yellow]"
            )

    try:
        merge_spack_layers(
            lockfile_path=lockfile_path,
            base_image=base_image,
            oci_url=oci_url,
            dest_image=dest_image,
            username=username,
            password=password,
            debug=debug,
            max_workers=max_workers,
            flatten=flatten,
        )

        # Show cache stats
        if debug:
            cache_files = list(CACHE_DIR.glob("*.json")) if CACHE_DIR.exists() else []
            console.print(f"\n[bold]Cache statistics:[/bold]")
            console.print(f"  Cache directory: {CACHE_DIR}")
            console.print(f"  Cached manifests: {len(cache_files)}")

    except Exception as e:
        console.print(f"\n[red bold]Error:[/red bold] {e}")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
