#!/usr/bin/env bash
set -euo pipefail

N=5
DELAY=2

for i in $(seq 1 $N); do
    echo "Attempt $i/$N..."
    if "$@"; then
        echo "Command succeeded on attempt $i."
        exit 0
    else
        echo "Command failed on attempt $i."
        if [ "$i" -lt $N ]; then
            echo "Retrying in $DELAY seconds..."
            sleep $DELAY
        fi
    fi
done

echo "Command failed after $N attempts."
exit 1
