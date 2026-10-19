# Portable image validation — October19,2026

The Dockerfile in this repository built successfully on a Linux Docker host
using its published dependency sources. The Kokoro source-asserted alignment
workaround applied and `uv pip check` passed. Observed Python3.12.15,
Torch2.14.0+xpu, selected Intel Arc Pro B50 for both workers.

Two disposable containers ran the new image with existing pinned model files
mounted read-only, no published host ports, a separate temporary Docker network
and a temporary bearer key. Existing speech, LLM and image services were not
restarted. Candidate containers and network were removed after testing.

| Check | Result |
|---|---|
|TTS and STT device identity|Both identified B50|
|Missing bearer key on public API|401, rejected|
|WAV synthesis|325244bytes;6.775s audio; valid RIFF header|
|MP3 synthesis|27404bytes;6.775s source audio|
|PCM synthesis|325200bytes;6.775s audio|
|Empty STT language / automatic detection|Returned expected English transcript|
|Dependency consistency|Passed|

Fixed prompt: “The living room lights are on. I have set a timer for five
minutes. Is there anything else you would like me to do?” Recognition returned
the same sentence text. The first WAV call took5.746seconds including initial
inference; subsequent MP3/PCM synthesis headers reported0.1645/0.1576seconds.
Recognition wall time was0.315seconds. These are single smoke observations,
not repeated performance measurements or a new hardware comparison.

CI additionally checks Python/JSON/YAML, local documentation links, credential
and personal-email patterns in published files/history, lint and nine pure
language/authentication tests. CI has no GPU and cannot reproduce hardware checks.

The image/application was exercised with explicit disposable Docker commands;
the Compose file is a portable deployment example, not a separately exercised
new host installation. Both Compose examples were rendered/validated separately.
The downloader's pinned sources are the measured model revisions; this check
reused existing weights and did not redownload them. Natural-speaker accuracy,
Russian/Ukrainian recordings, browser microphone/playback, concurrent workloads
and other Arc cards remain unvalidated here. No quality guarantee is inferred.
