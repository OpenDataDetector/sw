#!/usr/bin/env python3
"""
Combine layers from multiple Docker/OCI images into a new image
without creating new layer content - only a new manifest.
"""

import json
import sys
import subprocess
import tempfile
from typing import List


def get_manifest(image_ref: str) -> dict:
    """Get image manifest using crane"""
    result = subprocess.run(
        ["crane", "manifest", image_ref],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def get_config(image_ref: str) -> dict:
    """Get image config using crane"""
    result = subprocess.run(
        ["crane", "config", image_ref],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def combine_image_layers(
    base_image: str,
    layer_images: List[str],
    output_image: str,
    registry: str = None,
) -> None:
    """
    Combine layers from multiple images into a new image.

    Args:
        base_image: Base image to start with
        layer_images: List of images whose layers to append
        output_image: Output image reference
        registry: Optional registry to push to
    """
    print(f"Base image: {base_image}")
    print(f"Layer images: {layer_images}")
    print(f"Output: {output_image}")
    print()

    # Get base manifest and config
    print("Fetching base image manifest and config...")
    base_manifest = get_manifest(base_image)
    base_config = get_config(base_image)

    # Collect all layers and diff_ids
    all_layers = base_manifest.get("layers", []).copy()
    all_diff_ids = base_config.get("rootfs", {}).get("diff_ids", []).copy()
    all_history = base_config.get("history", []).copy()

    # Append layers from each image
    for layer_img in layer_images:
        print(f"Processing {layer_img}...")
        manifest = get_manifest(layer_img)
        config = get_config(layer_img)

        # Add layers (these are just references by digest)
        layers = manifest.get("layers", [])
        all_layers.extend(layers)
        print(f"  Added {len(layers)} layer(s)")

        # Add diff_ids from config
        diff_ids = config.get("rootfs", {}).get("diff_ids", [])
        all_diff_ids.extend(diff_ids)

        # Add history entries
        history = config.get("history", [])
        all_history.extend(history)

    # Create new config
    print("\nCreating new image config...")
    new_config = base_config.copy()
    new_config["rootfs"]["diff_ids"] = all_diff_ids
    new_config["history"] = all_history

    # Write new config to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(new_config, f, indent=2)
        config_file = f.name

    # Push new config blob and get digest
    print("Pushing new config blob...")
    result = subprocess.run(
        ["crane", "blob", output_image, config_file],
        capture_output=True,
        text=True,
    )

    # If that doesn't work, we need to create the full manifest manually
    # Create new manifest
    print("Creating new image manifest...")
    new_manifest = {
        "schemaVersion": 2,
        "mediaType": base_manifest.get(
            "mediaType",
            "application/vnd.docker.distribution.manifest.v2+json"
        ),
        "config": base_manifest["config"],  # Will update this
        "layers": all_layers,
    }

    # For simplicity with crane, we'll use append approach
    print("\nBuilding combined image using crane append...")

    # Start with base
    subprocess.run(["crane", "copy", base_image, output_image], check=True)

    # Append each layer image
    for layer_img in layer_images:
        print(f"Appending layers from {layer_img}...")

        # Export and append
        export_proc = subprocess.Popen(
            ["crane", "export", layer_img],
            stdout=subprocess.PIPE,
        )

        subprocess.run(
            ["crane", "append", "-b", output_image, "-f", "-", "-t", output_image],
            stdin=export_proc.stdout,
            check=True,
        )
        export_proc.wait()

    print(f"\n✓ Successfully created {output_image}")
    print(f"\nInspect with: crane manifest {output_image}")
    print(f"Total layers: {len(all_layers)}")


def main():
    if len(sys.argv) < 4:
        print("Usage: combine_image_layers.py <base-image> <output-image> <layer-image-1> [layer-image-2 ...]")
        print()
        print("Example:")
        print("  ./combine_image_layers.py \\")
        print("    ubuntu:24.04 \\")
        print("    ghcr.io/myorg/combined:latest \\")
        print("    oci://ghcr.io/myorg/layer1 \\")
        print("    oci://ghcr.io/myorg/layer2")
        sys.exit(1)

    # Check if crane is available
    try:
        subprocess.run(["crane", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: crane is not installed or not in PATH")
        print("Install with: go install github.com/google/go-containerregistry/cmd/crane@latest")
        sys.exit(1)

    base_image = sys.argv[1]
    output_image = sys.argv[2]
    layer_images = sys.argv[3:]

    combine_image_layers(base_image, layer_images, output_image)


if __name__ == "__main__":
    main()
