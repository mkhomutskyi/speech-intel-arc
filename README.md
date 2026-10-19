# Local TTS and STT on Intel Arc GPUs

Kokoro speech synthesis on **PyTorch XPU** and Whisper recognition on
**OpenVINO GenAI**, isolated into separate service processes. OpenAI-style
audio endpoints work with OpenWebUI and other local assistant clients.

**Measured hardware: Intel Arc Pro B50,16GB.** Other Intel Arc cards have not
been validated in this project. This is an independent speech project, not a
CUDA Speaches fork and not an LLM runner.

| Start here | What it covers |
|---|---|
| [Setup guide](docs/setup.md) | Host prerequisites, exact pins, model preparation and startup |
| [Measurements](docs/measurements.md) | October18 results, cold/warm distinctions and limits |
| [Runtime options](docs/runtime-options.md) | Custom API versus Speaches; tested OpenVINO-only TTS candidate |
| [OpenWebUI integration](docs/openwebui.md) | TTS/STT URLs, voices, language behavior and HTTPS |
| [Troubleshooting](docs/troubleshooting.md) | Device selection, alignment workaround, language and memory |

## Quick start

Linux/Docker Compose, an Intel GPU supported by the host kernel and compute
runtime, and Python3.12+ for the download/smoke scripts are required. Check
your exact GPU device nodes and ownership before editing the example.

```bash
git clone https://github.com/mkhomutskyi/speech-intel-arc.git
cd speech-intel-arc
cp .env.example .env
# Set actual CARD_DEVICE, RENDER_DEVICE, RENDER_GID and device selectors.
python3 scripts/download_models.py
docker compose config --quiet
docker compose build stt
docker compose up -d
curl -fsS http://127.0.0.1:8880/health
python3 scripts/smoke.py --output evidence/first-roundtrip
```

`download_models.py` explicitly downloads pinned public Kokoro/Whisper weights,
records SHA256 hashes and verifies available upstream size/LFS hashes. Review
model licenses before running it. Weights are not part of this repository.
Both inference services mount them read-only and run with HF offline mode.
The API binds localhost by default; only the proxy exposes a host port.

## Scope and validation

The working B50 implementation and longer utterance/format tests were verified
October18,2026. This October19 packaging generalizes model paths/device settings,
adds optional bearer authentication and forwards empty STT language as automatic
detection. See the setup guide for the separate clean-package validation status.
The [new image passed isolated B50 TTS/STT acceptance](docs/validation.md). It does not silently modify an existing speech deployment.

The enabled TTS voice is **English af_sky**; Russian/Ukrainian TTS is not claimed.
Whisper passed six natural-speaker recordings across English, Russian and
Ukrainian, with both automatic detection and explicit language selection.
See the [validation record](docs/validation.md) for errors and sample limits.
Real microphone acceptance is still required; six clips cannot establish
general accent/noise quality.
Models stay loaded in their worker processes for low latency; concurrent image,
LLM and audio-generation jobs can contend for the same GPU.

## Endpoints

- `GET /health` — selected TTS device, Torch version and model revision.
- `GET /v1/models` — speech model IDs.
- `POST /v1/audio/speech` — JSON input, voice af_sky, pcm/wav/mp3 output.
- `POST /v1/audio/transcriptions` — multipart audio upload, optional language,
  JSON transcript.25MiB/five-minute limits; STT decoding is greedy.

Original glue/scripts/documentation: Apache-2.0. Upstream packages and weights
retain their licenses; [NOTICE](NOTICE) identifies sources. Read [SECURITY.md](SECURITY.md).

Separate projects: [Illama2](https://github.com/mkhomutskyi/illama2) for LLMs,
[ComfyUI on Arc](https://github.com/mkhomutskyi/comfyui-intel-arc) for images.

