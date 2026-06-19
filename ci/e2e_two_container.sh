#!/bin/bash
# =============================================================================
# End-to-end TWO-CONTAINER test: sim image  --(file handoff)-->  reco image.
# =============================================================================
# The single-container smoke tests prove each image runs in isolation. This proves
# the part neither of them can: the *handoff*. The sim image's podio writes an
# edm4hep file that the reco image's podio (1.4.1) must read, with geometry-
# consistent calo cellIDs, all the way through Pandora to PFOs. Those are exactly
# the failure modes that only ever showed up across the boundary (cross-version
# podio bad_function_call; dropped cellID metadata; geometry DetType mismatch).
#
# It mirrors the production chain but runs the calo-only (neutral) Pandora path.
# The charged path additionally needs acts_tracking.py + add_metadata_frames.py,
# which live in the ColliderML-Production repo, not here; the calo-only path still
# exercises the genuine sim->reco podio + geometry handoff, which is the point.
#
# Geometry: both images must decode the SAME calo cellIDs. We use the calibrated
# azaborow ODD (addLayeredCalo_MuonCoil) on BOTH sides. The .so is DD4hep-ABI-
# specific, so each image needs its OWN build of it: the reco image already bakes
# one at /opt/odd-install; here we build a matching one INSIDE the sim image from
# the same XML/branch (identical cellIDs, just compiled against the sim DD4hep).
#
# Usage:  ci/e2e_two_container.sh <sim_image> <reco_image> [n_events]
# Needs:  docker; a runner that can hold both images (~25 GB each) + run Geant4.
#         Both images must already be pulled.
# =============================================================================
set -euo pipefail

SIM_IMAGE="${1:?usage: e2e_two_container.sh <sim_image> <reco_image> [n_events]}"
RECO_IMAGE="${2:?usage: e2e_two_container.sh <sim_image> <reco_image> [n_events]}"
NEV="${3:-2}"

ODD_REPO="https://gitlab.cern.ch/azaborow/OpenDataDetector.git"
ODD_REF="addLayeredCalo_MuonCoil"

WORK="$(mktemp -d)"
chmod 777 "$WORK"          # the two images run as different uids; both write here
trap 'rm -rf "$WORK"' EXIT
echo "sim=$SIM_IMAGE  reco=$RECO_IMAGE  nev=$NEV  work=$WORK"

# ---------------------------------------------------------------------------
# Phase 1 (SIM container): build the calibrated ODD against this image's DD4hep,
# then ddsim a few gun events into the calorimeter -> /work/sim.root.
# ---------------------------------------------------------------------------
echo "::group::sim container — build ODD + ddsim"
docker run --rm -v "$WORK:/work" -e NEV="$NEV" -e ODD_REPO="$ODD_REPO" -e ODD_REF="$ODD_REF" \
  "$SIM_IMAGE" bash -lc '
    set -euo pipefail
    # sw images bake their env into PATH; be tolerant if a profile script is needed.
    for p in /etc/profile.d/*.sh; do [ -f "$p" ] && source "$p" || true; done
    command -v ddsim >/dev/null || { echo "ddsim not found in sim image PATH"; exit 3; }
    git clone --depth 1 --single-branch --branch "$ODD_REF" "$ODD_REPO" /tmp/odd-src
    cmake -S /tmp/odd-src -B /tmp/odd-build -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX=/tmp/odd
    cmake --build /tmp/odd-build -j"$(nproc)" --target install
    DET=/tmp/odd/share/OpenDataDetector/xml/OpenDataDetector.xml
    test -f "$DET"
    ddsim --compactFile "$DET" --enableGun --gun.distribution uniform \
          --gun.particle pi- --gun.energy "10*GeV" \
          --gun.thetaMin "60*deg" --gun.thetaMax "120*deg" \
          --numberOfEvents "$NEV" --random.seed 42 --outputFile /work/sim.root
    ls -l /work/sim.root
  '
echo "::endgroup::"
[ -s "$WORK/sim.root" ] || { echo "FAIL: sim image did not write sim.root"; exit 1; }

# ---------------------------------------------------------------------------
# Phase 2 (RECO container): Pandora calo-only PF on the SIM-WRITTEN file.
# This is where a cross-version podio read / missing cellID metadata would blow up.
# ---------------------------------------------------------------------------
echo "::group::reco container — Pandora calo PF on the sim-written file"
docker run --rm -v "$WORK:/work" -e NEV="$NEV" \
  "$RECO_IMAGE" bash -lc '
    set -euo pipefail
    source /opt/key4hep-shim.sh
    source /opt/pandora-stack/install/setup_stack.sh
    export K4ODD_PATH=/opt/k4ODD ODD_INSTALL_DIR=/opt/odd-install
    export LD_LIBRARY_PATH=/opt/k4ODD/install/lib:/opt/k4ODD/install/lib64:${LD_LIBRARY_PATH:-}
    export PYTHONPATH=/opt/k4ODD/install/python:${PYTHONPATH:-}
    # calo-only: CreateEmptyTracks (default) + the Minimal settings
    export K4ODD_TRACK_COLLECTION=EmptyTracks
    export K4ODD_PANDORA_SETTINGS=/opt/k4ODD/k4ODD/options/PandoraSettingsMinimal.xml
    k4run /opt/k4ODD/k4ODD/options/ODDreconstruction.py \
          --inputFile /work/sim.root --outputFile /work/reco.root --num-events "$NEV"
    podio-dump /work/reco.root | tee /work/dump.txt
  '
echo "::endgroup::"
[ -s "$WORK/reco.root" ] || { echo "FAIL: reco image did not write reco.root"; exit 1; }

# ---------------------------------------------------------------------------
# Assert PFOs came out of the sim-written file.
# ---------------------------------------------------------------------------
rc=0
for coll in GaudiPandoraPFOs GaudiPandoraClusters; do
  if grep -q "$coll" "$WORK/dump.txt"; then echo "  OK  $coll"
  else echo "  FAIL missing $coll"; rc=1; fi
done
[ "$rc" -eq 0 ] && echo "E2E TWO-CONTAINER TEST PASSED" || { echo "E2E TWO-CONTAINER TEST FAILED"; exit 1; }
