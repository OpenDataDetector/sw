#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}"   )" &> /dev/null && pwd   )

uv run "${SCRIPT_DIR}/_download_geant4_datasets.py"
