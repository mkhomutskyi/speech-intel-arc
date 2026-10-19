# Setup and reproducibility

## Tested baseline

The reference implementation ran on Ubuntu26.04 in a Docker-enabled Linux guest
with an Arc Pro B50 exposed as DRM card/render nodes. On a normal Linux host,
no Proxmox layer is needed. A container shares its host's kernel: installing
userspace packages in Docker does not add support for an unsupported host GPU.
For LXC, first arrange host DRM access and guest permissions; this repository
does not change the hypervisor or require privileged Docker/AppArmor bypasses.

Identify the GPU using `lspci -D`, `ls -l /dev/dri/by-path` and
`stat -c '%n %g' /dev/dri/card* /dev/dri/renderD*`. Map only the intended
card/render nodes in .env. Do not assume renderD128 or GPU0 means the B50.
Container health responses must identify the intended card, not another iGPU.

Direct runtime pins observed on the working service:

| Component | Pin |
|---|---|
|Python|3.12 series|
|Torch|2.14.0+xpu from PyTorch's XPU index|
|OpenVINO|2026.5.0.dev20261015|
|GenAI / Tokenizers|2026.5.0.0.dev20261015|
|Kokoro / Misaki|0.9.4 /0.9.4|
|FastAPI / Uvicorn|0.143.5 /0.54.0|
|NumPy / PyAV|2.5.4 /19.0.1|
|Transformers / HF Hub|5.20.1 /2.2.0|
|English spaCy model|en_core_web_sm3.8.0|

Torch and OpenVINO use different runtimes; keep TTS and STT in separate
processes even when sharing one image. The three OpenVINO packages are one ABI
family and must be changed together. These are measured pins, not an assertion
that the latest available packages are always compatible. requirements.txt pins
direct application dependencies; it is not a complete transitive dependency lock.

## Model preparation

The downloader uses these exact publicly available revisions:

- hexgrad/Kokoro-82M: f3ff3571791e39611d31c381e3a41a3af07b4987; config,
  native weights and af_sky voice only.
- OpenVINO/whisper-large-v3-turbo-fp16-ov:
  0250c28d68c7c10d6b5cb39707e876c0c66ab6f8; published OpenVINO XML/BIN plus
  supporting text/config files. No local export or HF remote modeling code is required.

It writes data/models/kokoro, data/models/whisper and model-manifest.json with
portable relative filenames, byte sizes and SHA256s. Preserve that manifest with
your deployment evidence. Do not put a machine-specific absolute path manifest
from another installation into this package. Public model access/network is
needed only during download and image build; normal inference is configured offline.

## Build, select, start

Copy .env.example and edit actual nodes and the render-node group ID. The
reference image runs as root inside Docker and adds the render group once;
card and render nodes may have the same group ID in an LXC. Non-root execution
needs its own device-permission validation. `XPU_DEVICE=xpu:0` and
`OV_DEVICE=GPU` are defaults, not stable hardware identities. The expected-name
check defaults to Arc and can be set to B50 for a stricter local check.
Use FP32 first; BF16 is optional and must be checked with your utterances.

Run the README commands. STT loads first; the speech service waits for STT
health. Initial model compilation and the first synthesis can take much longer
than warmed measurements. Send a warmup request before measuring steady state.
Use a new evidence directory for each smoke run, then listen to speech.wav.
SPEECH_DATA is relative to the Compose project unless you give an absolute path.

For clients outside the Docker host, select a reachable local bind address and
set a private SPEECH_API_KEY. Add that same key to the audio client's settings.
Do not expose an unauthenticated port to the internet. Use an authenticated HTTPS
gateway for remote access. The internal STT worker has no published host port;
do not attach untrusted containers to its network.

## Validation status

The original B50 TTS/STT implementation and alignment workaround passed actual
GPU generation/recognition and synthesis-format/long-utterance checks onOctober18.
The portable October19 packaging is separately tracked in the repository's
[validation record](validation.md); static/CPU CI cannot prove fresh image builds, GPU access,
microphone recognition or subjective voice quality. Follow its smoke procedure
on your own host before relying on the service.

## Updating and rollback

Keep the previous image tag, .env and model hashes. Build a new candidate tag,
run dependency checks, inspect selected GPU names and test short/long utterances,
all formats, language forwarding and the same recordings. Only then replace the
service image. Never upgrade Torch inside a running container or mix mismatched
OpenVINO wheels. `docker compose down` preserves named caches and model files;
do not use volume deletion as an update procedure.

Sources: [PyTorch Intel GPU guide](https://docs.pytorch.org/docs/main/notes/get_start_xpu.html),
[OpenVINO WhisperPipeline](https://docs.openvino.ai/2025/api/genai_api/_autosummary/openvino_genai.WhisperPipeline.html),
[Kokoro](https://huggingface.co/hexgrad/Kokoro-82M),
[Whisper export](https://huggingface.co/OpenVINO/whisper-large-v3-turbo-fp16-ov).

