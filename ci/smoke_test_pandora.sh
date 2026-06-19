#!/bin/bash
# Self-contained smoke test for the Pandora (reco) image. Runs INSIDE the built image
# (no external fixture, no sim image): the image already ships ddsim + Geant4 data + the
# baked azaborow ODD + the calibrated Pandora stack. Sims a couple of gun events, runs
# Pandora calo-only particle flow, and asserts GaudiPandoraPFOs come out. Exits non-zero
# on any failure so CI fails loudly.
#
# This exercises the parts that were hard to port off cvmfs: native key4hep activation,
# the source-built k4Reco link, the calo DetType geometry, the Pandora settings path, and
# the k4FWCore/Gaudi-40 k4run fix.
set -euo pipefail

echo "::group::activate env + presence checks"
source /opt/key4hep-shim.sh
source /opt/pandora-stack/install/setup_stack.sh
export K4ODD_PATH=/opt/k4ODD
export ODD_INSTALL_DIR=/opt/odd-install
# ODD ships a setup script under bin/ (name varies by ODD version); geometry itself
# resolves via ODD_INSTALL_DIR, so source it best-effort and don't fail if absent.
for s in /opt/odd-install/bin/this*ODD*.sh /opt/odd-install/bin/this_odd.sh; do
  [ -f "$s" ] && source "$s" && break
done
export LD_LIBRARY_PATH=/opt/k4ODD/install/lib:/opt/k4ODD/install/lib64:${LD_LIBRARY_PATH:-}
export PYTHONPATH=/opt/k4ODD/install/python:${PYTHONPATH:-}
# Executables must be on PATH; the calibrated geometry XML must exist exactly.
for f in "$(command -v k4run)" "$(command -v ddsim)" "$(command -v podio-dump)" \
         /opt/odd-install/share/OpenDataDetector/xml/OpenDataDetector.xml ; do
  [ -n "$f" ] && [ -e "$f" ] || { echo "MISSING: $f"; exit 1; }
done
# Plugin libs: tolerate lib/ vs lib64/ across the prefixes.
need_lib() {
  for p in "$@"; do find "$p"/lib "$p"/lib64 -name "$lib" 2>/dev/null | grep -q . && return 0; done
  echo "MISSING lib: $lib (searched: $*)"; return 1
}
lib=libk4GaudiPandoraPlugins.so need_lib /opt/pandora-stack/install || exit 1
lib=libGaudiTrkUtils.so          need_lib /opt/k4reco-install        || exit 1
lib=libk4ODDPlugins.so           need_lib /opt/k4ODD/install         || exit 1
echo "PANDORA_STACK_PREFIX=${PANDORA_STACK_PREFIX:-UNSET}"
echo "::endgroup::"

WORK=$(mktemp -d)
DET=/opt/odd-install/share/OpenDataDetector/xml/OpenDataDetector.xml

echo "::group::ddsim (2 x 10 GeV pi- into the calo, azaborow ODD)"
cd /opt/k4ODD
ddsim --compactFile "$DET" --steeringFile k4ODD/options/ODDsimulation.py \
  --enableGun --gun.distribution uniform --gun.energy "10*GeV" --gun.particle pi- \
  --gun.thetaMin "60*deg" --gun.thetaMax "120*deg" \
  --numberOfEvents 2 --outputFile "$WORK/sim.root" --random.seed 42
echo "::endgroup::"

echo "::group::Pandora particle flow (calo-only)"
export K4ODD_TRACK_COLLECTION=EmptyTracks
export K4ODD_PANDORA_SETTINGS=/opt/k4ODD/k4ODD/options/PandoraSettingsMinimal.xml
k4run /opt/k4ODD/k4ODD/options/ODDreconstruction.py \
  --inputFile "$WORK/sim.root" --outputFile "$WORK/reco.root" --events 2
echo "::endgroup::"

echo "::group::assert PFO collections"
DUMP=$(podio-dump "$WORK/reco.root" 2>/dev/null)
rc=0
for coll in GaudiPandoraPFOs GaudiPandoraClusters GaudiPandoraStartVertices; do
  if echo "$DUMP" | grep -q "$coll"; then
    echo "  OK  $coll"
  else
    echo "  FAIL missing $coll"; rc=1
  fi
done
echo "::endgroup::"
[ "$rc" -eq 0 ] && echo "SMOKE TEST PASSED" || { echo "SMOKE TEST FAILED"; exit 1; }
