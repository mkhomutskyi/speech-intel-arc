# Portable image validation — October 19, 2026

## Fresh download and Compose acceptance

A fresh public checkout, empty model directory and the published downloader
were exercised on the B50. Every required model file downloaded and passed
the script's upstream size/LFS-hash checks; the generated manifest recorded
SHA256s. The published Dockerfile built, and the Compose project started both
workers healthy with read-only model mounts and a private test bearer key.
The corrected Compose configuration also passed with equal card/render GIDs,
as found on the test LXC. Production workloads were kept running during these
candidate tests; later a separate speech-only production patch was validated.

| Check | Observed result |
|---|---|
|Published smoke client|TTS/STT round trip passed|
|WAV / PCM / MP3|All returned valid responses; WAV mono, 24 kHz, signed 16-bit|
|Long TTS|63.9 seconds of audio generated in 3.260 seconds wall time|
|Empty text, wrong voice/format, invalid speed|422|
|Missing/wrong bearer key|401|
|Invalid language / upload over 25 MiB|422 / 413|
|Invalid audio|Initially exposed a proxy bug (502); corrected image retest returned 400|
|Simultaneous TTS and STT, three pairs|All 200; TTS 0.270–0.271 s, STT 0.205–0.208 s|
|Restart both candidate services|TTS/STT recovered; model manifest unchanged|
|Browser-style input|48 kHz stereo WebM/Opus decoded; Ukrainian transcript returned|
|Long recognition|63.9-second synthetic clip transcribed in 1.062 seconds|
|Over-duration input|300.1-second WAV rejected with 413 before inference|
|Official native OpenVINO Kokoro on B50|Generated audio without importing Torch; Whisper recognized its expected text|

### Human recordings

Source: [Google FLEURS](https://huggingface.co/datasets/google/fleurs), test
split, revision `70bb2e84b976b7e960aa89f1c648e09c59f894dd`. The first two
archive members matching test.tsv labels were selected per language, without
cherry-picking. The dataset preview endpoint failed, so original TSV/audio
archives were used. Each clip was tested twice, with blank automatic detection
and an explicit en/ru/uk parameter. All twelve requests returned transcripts;
auto and explicit output matched for these fixtures.

| Language | Clips | Total reference words | Word edits | WER | Auto wall time per clip |
|---|---:|---:|---:|---:|---|
|English|2|40|3|7.50%|0.154–0.163 s|
|Russian|2|35|0|0.00%|0.184–0.258 s|
|Ukrainian|2|24|1|4.17%|0.164–0.199 s|

WER uses Unicode NFKC, case folding, punctuation replaced by spaces,
whitespace word splitting and Levenshtein edits, divided by reference words.
No number verbalization or additional language-specific normalization was
applied. English included the reference's singular "year" versus recognized
"years" and a German word; Ukrainian had one differing word. **Two clips per
language are a functional check, not a representative accuracy benchmark.**
Audio duration ranged 7.08–16.92 seconds. Timings include local HTTP upload,
decoding and inference with resident models; no browser or external proxy.

Sanitized per-call results, recording IDs/hashes, runtime pins and the initial
failure/retest are in [validation.json](../benchmarks/2026-10-19/validation.json).
Recordings are not redistributed here. FLEURS attribution/license remains with
the upstream dataset. The [runtime investigation](runtime-options.md) gives the
official candidate model revision, reproducible probe and migration limits.

The live reference service separately passed omitted-language English/Russian/
Ukrainian requests after its English default was removed. Its PyTorch/OpenVINO
engines were retained, and the prior image was kept for rollback.

### Remaining boundaries

OpenWebUI read-aloud also passed using a normal signed-in owner browser session:
its audio element reached readyState4, played to3.96s of4.512s, with no media
error. This checks browser delivery/playback state, not human listening quality.

The owner then confirmed hearing the voice and using the microphone. The
resulting English message and assistant response were visible in the temporary
chat. Both OpenWebUI audio routes and their upstream B50 speech/transcription
routes returned200. This completes one owner-assisted English microphone and
audible-playback check; no objective speech-quality score is inferred.

Physical Russian/Ukrainian microphone trials, detailed voice-quality evaluation,
family-user controls,
simultaneous music/SFX/image/LLM contention,
other Arc cards and an NPU deployment remain outside these checks. The
OpenVINO-only probe is not a complete replacement API. No broader guarantee is inferred.

## Earlier disposable-image smoke

The Dockerfile in this repository built successfully on a Linux Docker host
using its published dependency sources. The Kokoro source-asserted alignment
workaround applied and `uv pip check` passed. Observed Python 3.12.15,
Torch 2.14.0+xpu, selected Intel Arc Pro B50 for both workers.

Two disposable containers ran the new image with existing pinned model files
mounted read-only, no published host ports, a separate temporary Docker network
and a temporary bearer key. Existing speech, LLM and image services were not
restarted. Candidate containers and network were removed after testing.

| Check | Result |
|---|---|
|TTS and STT device identity|Both identified B50|
|Missing bearer key on public API|401, rejected|
|WAV synthesis|325244bytes; 6.775s audio; valid RIFF header|
|MP3 synthesis|27404bytes; 6.775s source audio|
|PCM synthesis|325200bytes; 6.775s audio|
|Empty STT language / automatic detection|Returned expected English transcript|
|Dependency consistency|Passed|

Fixed prompt: “The living room lights are on. I have set a timer for five
minutes. Is there anything else you would like me to do?” Recognition returned
the same sentence text. The first WAV call took5.746 seconds including initial
inference; subsequent MP3/PCM synthesis headers reported0.1645/0.1576 seconds.
Recognition wall time was0.315 seconds. These are single smoke observations,
not repeated performance measurements or a new hardware comparison.

CI additionally checks Python/JSON/YAML, local documentation links, credential
and personal-email patterns in published files/history, lint, request helper
tests and an equal-GID Compose regression. CI has no GPU and cannot reproduce
hardware checks.

That earlier image smoke used explicit Docker commands and reused weights.
The fresh-download/Compose and natural-recording checks above supersede those
earlier packaging gaps. Neither run validates other hardware or subjective quality.


## October 29 publication rehearsal

The [dated publication check](publication-check-2026-10-29.md) reuses the pinned
public fixtures and verifies the cache-corrected recipe on B50. Raw data, local
addresses, temporary keys and owner recordings are excluded from this repository.
The October 19 owner-assisted English microphone/playback acceptance remains a
dated observation; no new physical microphone or subjective listening score is
claimed by the publication rehearsal.
