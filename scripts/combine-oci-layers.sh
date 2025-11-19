#!/bin/bash
# Combine multiple OCI image layers into a single image without creating new layers

set -e

BASE_IMAGE="${1:-ubuntu:24.04}"
OUTPUT_IMAGE="${2:-combined:latest}"
shift 2
LAYER_IMAGES=("$@")

if [ ${#LAYER_IMAGES[@]} -eq 0 ]; then
    echo "Usage: $0 <base-image> <output-image> <layer-image-1> [layer-image-2 ...]"
    echo "Example: $0 ubuntu:24.04 myapp:latest oci://ghcr.io/repo/layer1 oci://ghcr.io/repo/layer2"
    exit 1
fi

# Check if crane is installed
if ! command -v crane &> /dev/null; then
    echo "Error: crane is not installed"
    echo "Install with: go install github.com/google/go-containerregistry/cmd/crane@latest"
    exit 1
fi

echo "Base image: $BASE_IMAGE"
echo "Output image: $OUTPUT_IMAGE"
echo "Layer images: ${LAYER_IMAGES[*]}"

# Start with base image
echo "Copying base image..."
crane copy "$BASE_IMAGE" "$OUTPUT_IMAGE"

# Append each layer image
for layer_img in "${LAYER_IMAGES[@]}"; do
    echo "Appending layers from: $layer_img"

    # Export layers from the source image and append to target
    crane append \
        -b "$OUTPUT_IMAGE" \
        -f <(crane export "$layer_img") \
        -t "$OUTPUT_IMAGE"
done

echo "Successfully created $OUTPUT_IMAGE with all layers!"
echo ""
echo "Inspect with: crane manifest $OUTPUT_IMAGE"
echo "Or: docker pull $OUTPUT_IMAGE && docker history $OUTPUT_IMAGE"
