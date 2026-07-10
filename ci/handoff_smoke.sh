#!/bin/bash
# =============================================================================
# Cross-image HANDOFF smoke: sim image writes edm4hep, reco image reads it.
# =============================================================================
# This is deliberately THIN. It guards exactly one thing the per-image smoke
# tests can't: that a podio/edm4hep file written by the SIM image is readable by
# the RECO image's *different* podio build (this is where the cross-version
# `bad_function_call` on readEntry bit us). It does NOT run the pipeline.
#
# The real charged-PF two-container e2e (ddsim -> digi_and_reco ACTS tracking ->
# pandora_reco -> PFOs) lives in the ColliderML-Production repo, which owns those
# stages. Do not grow this into a pipeline test; keep it a handoff check.
#
# Usage:  ci/handoff_smoke.sh <sim_image> <reco_image> [n_events]
# Needs:  docker; both images already pulled.
# =============================================================================
set -euo pipefail

SIM_IMAGE="${1:?usage: handoff_smoke.sh <sim_image> <reco_image> [n_events]}"
RECO_IMAGE="${2:?usage: handoff_smoke.sh <sim_image> <reco_image> [n_events]}"
NEV="${3:-2}"

WORK="$(mktemp -d)"; chmod 777 "$WORK"; trap 'rm -rf "$WORK"' EXIT
echo "sim=$SIM_IMAGE  reco=$RECO_IMAGE  nev=$NEV  work=$WORK"

# ---- SIM image: ddsim a few gun events with the image's own bundled ODD -------
echo "::group::sim image — ddsim -> edm4hep.root"
docker run --rm -v "$WORK:/work" -e NEV="$NEV" "$SIM_IMAGE" bash -lc '
  set -euo pipefail
  for p in /etc/profile.d/*.sh; do [ -f "$p" ] && source "$p" || true; done
  command -v ddsim >/dev/null || { echo "ddsim not found in sim image"; exit 3; }
  # geometry: the sim image bundles the ODD; ask acts where it is (same resolver
  # ddsim_run.py uses when ODD_COMPACT_FILE is unset).
  DET=$(python3 -c "from acts.examples.odd import getOpenDataDetectorDirectory as d; print(d()/\"xml\"/\"OpenDataDetector.xml\")")
  test -f "$DET" || { echo "ODD compact not found at $DET"; exit 3; }
  ddsim --compactFile "$DET" --enableGun --gun.particle pi- --gun.energy "10*GeV" \
        --numberOfEvents "$NEV" --random.seed 1 --outputFile /work/edm4hep.root
  ls -l /work/edm4hep.root
'
echo "::endgroup::"
[ -s "$WORK/edm4hep.root" ] || { echo "FAIL: sim image did not write edm4hep.root"; exit 1; }

# ---- RECO image: read that file with the reco podio (the cross-version test) ---
echo "::group::reco image — podio reads the sim-written file"
docker run --rm -v "$WORK:/work" -e NEV="$NEV" "$RECO_IMAGE" bash -lc '
  set -euo pipefail
  source /opt/key4hep-shim.sh
  # podio-dump lists collections + metadata; the python read below actually pulls
  # every event (this is what throws bad_function_call if the formats are incompatible).
  podio-dump /work/edm4hep.root | tee /work/dump.txt
  python3 - <<PY
from podio.root_io import Reader
r = Reader("/work/edm4hep.root")
frames = r.get("events")
n = len(frames)
print(f"reco podio read {n} events from the sim-written file")
assert n >= int("'"$NEV"'"), f"expected >= {int(\"'"$NEV"'\")} events, got {n}"
f0 = frames[0]
colls = list(f0.getAvailableCollections())
print("collections:", colls)
# a calo SimHit collection must survive the handoff (geometry/cellID metadata path)
assert any("Cal" in c or "ECal" in c or "HCal" in c for c in colls), "no calo collection in handoff"
print("HANDOFF OK")
PY
'
echo "::endgroup::"
# The in-container python asserts (and `set -e` + docker exit-code propagation)
# already fail the run on a bad handoff; reaching here means it passed.
echo "CROSS-IMAGE HANDOFF SMOKE PASSED"
