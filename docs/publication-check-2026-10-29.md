# B50 publication rehearsal — October 29, 2026

This is the speech-only B50 reference recipe: Kokoro 82M af_sky/FP32 on PyTorch
XPU, and Whisper large-v3-turbo FP16 on OpenVINO GenAI. It does not describe
the author's separate application deployment or change its defaults.

Tested base source: `14d22d4fb903b97aa20f56328c0632693ea8489c`, plus the locally
reviewed Dockerfile/Compose cache correction. Its two-file runtime patch SHA256
is `f9bcb8dd05a58dee33744ed24c012a4964e27f357e2fedd29fd7cf0d4b4235ec`.
The release candidate is prepared locally for review. This record does not
claim it has been pushed or released; use the reviewed commit's identity when
deploying, and preserve the output of `git rev-parse HEAD`.

## What was exercised

A separate clone at the exact base commit used the published downloader against
isolated links to retained model files. Every required file passed its checks;
the original model manifest and file hashes were verified again after cleanup.
This was not a second fully empty download. The October 19 empty-download result
is retained as earlier evidence. Model revisions remain those in [setup](setup.md).

The original build succeeded, but startup exhausted the test filesystem while
populating a cache volume. The image also retained a large uv package cache.
The candidate adds `UV_NO_CACHE=1` and `volume.nocopy: true` for both runtime
caches. A new build, startup and the published smoke client then passed.
No inference code or direct runtime pin changed for this correction.

| Status | Check | Evidence boundary |
|---|---|---|
|Verified|Corrected image, Compose startup, published smoke|Actual two-worker B50 deployment; 127 service-environment packages compatible|
|Verified|GPU selection|Both workers matched the physical B50 identity; only its selected DRM nodes mapped; positive GPU compute activity in both workers|
|Verified|TTS|Short and long English af_sky, WAV mono 24 kHz/16-bit, nonzero audio; first plus 3 warm requests each|
|Verified|STT|Six public FLEURS clips, two per EN/RU/UK; known references and hashes; 3 additional warm repeats of one English clip|
|Verified|Cleanup|Test containers, network, new cache volumes, image, scoped build-cache records and temporary key removed; 9 existing container IDs unchanged and healthy|
|Historical verified|Owner microphone/playback|One English owner-assisted check on October 19, not repeated here|
|Historical verified|PCM/MP3, errors, concurrency, restart|October 19 checks; not a claim they were all rerun on October 29|
|Failed then corrected|Original cache-heavy startup|Storage exhaustion, not an inference/device-selection failure|
|Untested|Other Arc cards, physical RU/UK microphones, children/noise quality|No general accuracy or subjective-quality guarantee|
|Experimental|OpenVINO-only Kokoro|Native probe exists; complete replacement service remains unvalidated|

## Separate timing boundaries

| Task | Audio length | Model/frontend initialization | First request | Warm median, 3 requests |
|---|---:|---:|---:|---:|
|Kokoro short|4.450s|0.772s|3.082s|0.111s|
|Kokoro long|63.900s|Same loaded worker|3.207s, first long shape|1.443s|
|Whisper English|10.560s|1.990s|0.306s|0.156s|

Initialization timers surround model construction/transfer/frontend setup for
TTS and WhisperPipeline construction/compilation for STT. They exclude imports,
GPU plugin initialization and server readiness. Private staging-only timing
overlays added these timers without changing inference statements. Model files,
OS caches and runtime caches were retained. These are fresh-process timings,
not cold-disk startup. Complete-request wall time runs from local HTTP open
through fully read response; STT includes upload, proxy, decoding and inference.
Warm ranges: short 0.111–0.114 s, long 1.443–1.539 s, Whisper 0.154–0.156 s.
The first long request is not another model-cold start.

The TTS synthesis header includes handler lock wait, phonemization, inference,
synchronization and PCM conversion; container-format encoding happens afterward.
It is not pure GPU-kernel time or first-audible latency. Neither API is a
native streaming voice conversation interface.

## Content and memory

FLEURS test revision: `70bb2e84b976b7e960aa89f1c648e09c59f894dd`.
On the six reused clips, word edits/reference words were 3/40 English, 0/35 Russian
and 1/24 Ukrainian: 7.50%, 0%, 4.17%. NFKC, case folding, punctuation-to-spaces and
Levenshtein word edits were used, without number expansion. This small selected
subset is a functional check, not a representative WER benchmark.

Torch peak allocated memory was 999.6 MiB; end reserved memory 1272 MiB. OpenVINO
reported 1667.6 MiB `usm_device` at the final snapshot. Driver resident-VRAM
snapshots include different allocations and are not interchangeable with those
metrics; no continuous whole-card peak was measured. Both measured workers
used B50; CPU preprocessing and the small duration-alignment workaround remain.
Synthesis/transcription round trips do not establish subjective voice quality.

Test environment: Ubuntu 26.04.1 guest, Linux 7.0.14-26-pve with xe driver,
Intel Core Ultra 7 270K Plus, Arc Pro B50 16 GB, Docker 29.1.3, Compose 2.40.3.
Python 3.12.15, Torch 2.14.0+xpu, Kokoro/Misaki 0.9.4; the matched OpenVINO
2026.5 October 15 nightly family is unchanged. spaCy 3.8.18 and
en_core_web_sm3.8.0 were observed. These are observed prerequisites/versions,
not minimum supported kernel/CPU claims. Full transitive locks and raw results
remain private; readers should save their own manifest and `uv pip freeze` output.

FLEURS is by Google and distributed under
[CC BY4.0](https://huggingface.co/datasets/google/fleurs). Recordings are not
redistributed here. Kokoro, Whisper and their export authors retain their credits
and model licenses. See [NOTICE](../NOTICE).

## Final reader-command acceptance, same date

The exact command `docker compose up -d --wait --wait-timeout 300` returned
success with both workers healthy on Compose 2.40.3+ds1-0ubuntu1. Use a Compose
version supporting both flags; inspect `docker compose up --help`. The README
now waits before health/smoke requests and explains readiness diagnostics.

A separate final build, published smoke client, direct WAV request and one
known-reference English FLEURS transcription passed. Both workers matched the
same physical B50 and accumulated GPU compute cycles. The test mapped only
that card's canonical DRM nodes. The final 127-package freeze matched the earlier
rehearsal exactly; inference source and direct pins were unchanged.

The one explicit-English acceptance request had 1 edit in 19 reference words.
It is not a replacement for the six-clip automatic-language benchmark above.
No benchmark series or physical owner microphone check was repeated.
Temporary test resources were removed, original model hashes reverified and
all nine existing service container IDs remained unchanged and healthy.
