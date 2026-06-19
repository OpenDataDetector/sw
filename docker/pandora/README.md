# docker/pandora — the ColliderML reco (Pandora particle-flow) image

A second sw-repo image variant, built by `.github/workflows/build_pandora.yml` and pushed to
`ghcr.io/opendatadetector/sw` with a `pandora-` tag prefix (so it never collides with the
spack images from `build.yml`). It runs the calibrated **Pandora particle flow**
(`calo_digitization` + `pandora_reco`) for the ColliderML production pipeline.

## Why it is built differently from the spack images

The spack `sw` image's **ROOT 6.38 has no Eve component**. Production charged-PF Pandora needs
`k4GaudiPandora → k4Reco::GaudiTrkUtils → DDKalTest → KalTest`, and KalTest's `TRKTrack`
*inherits* `TEveTrackPropagator` — so KalTest cannot build against an Eve-less ROOT. The
key4hep stack is a *different ROOT build* (`+eve`) that production Pandora is welded to.

So this image is a plain `docker build` **FROM the key4hep no-cvmfs base**
(`ghcr.io/key4hep/key4hep-sim-reco-ubuntu24:reco-image-amd64` — ROOT 6.36 +eve, Gaudi 40,
k4FWCore 1.3, podio 1.4.1, edm4hep 0.99.2, DD4hep 1.32.1, prebuilt KalTest/DDKalTest/LCIO),
baking on top only the four small Pandora packages + k4Reco's `GaudiTrkUtils` + k4ODD + the
calibrated ODD geometry. The heavy stack is already in the base.

## Layout

`steps/*.sh` are each COPYed in their own layer right before their RUN (so editing a later
step doesn't invalidate earlier layers). Each is heavily commented with *why* its fix exists:

| Step | Why |
|------|-----|
| `key4hep-shim.sh`  | native key4hep activation + the source-built k4Reco prefix + a cvmfs-style merged-include CPATH |
| `build_k4reco.sh`  | k4Reco **v0.3.0** `GaudiTrkUtils` from source (base's spack k4reco has the wrong API + no CMake export) |
| `build_pandora.sh` | PandoraSDK / optimized LCContent / k4GaudiPandora / k4DetectorPerformance at pinned org-fork refs |
| `build_k4odd.sh`   | k4ODD plugins + calibrated options (`ODDreconstruction.py` / `ODDdigitisation.py`) |
| `patch_k4fwcore.sh`| guards `EventLoopMgr(Warnings=False)` — Gaudi 40 dropped it, which otherwise kills every `k4run` |
| `build_odd.sh`     | the calibrated `azaborow/addLayeredCalo_MuonCoil` ODD (kept LAST so re-bumping it keeps the Pandora cache) |

## CI

`build_pandora.yml` builds the image, runs `../../ci/smoke_test_pandora.sh` inside it
(ddsim a couple of gun events with the baked ODD → Pandora calo-only PF → assert
`GaudiPandoraPFOs`), and pushes only on `main`/tags after the test passes. Same triggers as
`build.yml` (push main/tags, PR touching this dir, manual dispatch, nightly cron).

## Build locally

```bash
docker build -t colliderml/reco:dev docker/pandora      # or `podman-hpc build` on Perlmutter
```
The build git-clones (k4ODD, ODD, Pandora forks) and apt-installs, so it needs internet.
