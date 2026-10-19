# Runtime choices and the Speaches question

The deployed reference is a small custom FastAPI adapter, not a Speaches fork.
It exposes one OpenAI-style speech API and isolates two inference engines:

| Task | Model | Current engine |
|---|---|---|
|English TTS|Kokoro-82M, af_sky|PyTorch XPU, FP32|
|Multilingual STT|Whisper large-v3-turbo|OpenVINO GenAI, FP16 export|

XPU is PyTorch's Intel GPU backend. XGBoost is unrelated to this implementation.
Speaches' documented Docker installation provides CPU and CUDA options; it was
not retained as the B50 serving layer. See [Speaches installation](https://speaches.ai/installation/).

## Can both use OpenVINO?

Yes: on October 19, 2026 the native GenAI Text2SpeechPipeline generated valid
24 kHz Kokoro audio on the B50 without importing Torch. Whisper transcribed the
first and last generated clips as the expected sentence. This validates a
candidate inference path, not a complete replacement API or subjective quality.

Candidate: [OpenVINO/Kokoro-82M-int8-ov](https://huggingface.co/OpenVINO/Kokoro-82M-int8-ov),
revision `9c035d0bfab136f0c1c525a5841d3411d7220c66`. Same af_sky voice and text
as the PyTorch smoke test; different weight precision and frontend, so waveform
equality is not expected. OpenVINO/GenAI/Tokenizers use the setup guide's matched
20261015 nightly pins. The native frontend needs **all four** us/gb gold/silver
JSON lexicons even for an American English voice.

With the repository image built and the candidate model downloaded at that
exact revision, run the optional probe separately from your production service:

```bash
hf download OpenVINO/Kokoro-82M-int8-ov \
  --revision 9c035d0bfab136f0c1c525a5841d3411d7220c66 \
  --local-dir ./candidate-kokoro-ov \
  --include config.json openvino_config.json openvino_model.xml openvino_model.bin \
  'data/*_gold.json' 'data/*_silver.json' voices/af_sky.bin
mkdir -p evidence
docker run --rm \
  --device "$CARD_DEVICE" --device "$RENDER_DEVICE" \
  -v "$PWD/candidate-kokoro-ov:/model:ro" \
  -v "$PWD/evidence:/out" \
  -v "$PWD/scripts/probe_openvino_tts.py:/probe.py:ro" \
  speech-intel-arc:20261019 python /probe.py \
  --model /model --output /out/openvino-candidate --expected-gpu B50
```

Set/export the two device variables from your actual hardware first. Run `hf`
in an environment with the pinned huggingface-hub dependency. This downloads
additional candidate weights and does not change Compose or its default model.
The probe refuses to overwrite its output directory. Preserve model revision,
file hashes, WAVs and result.json; listen and test your own longer utterances.

Observed compile time: 12.18 seconds. Five synthesis calls took 6.677, 1.756,
0.402, 0.270 and 0.364 seconds for 4.425 seconds of audio. PyTorch's warmed
synthesis headers for the same sentence reported 0.109–0.112 seconds for
4.45 seconds of audio. These short sequential observations are not a controlled
cross-runtime benchmark: different precision/frontends, cold shape compilation,
transport/encoding and other resident workloads affect the comparison.

Keep the mixed runtime as the default for now. It passed the broader API tests
and has the better observed warm synthesis latency. An OpenVINO-only deployment
is feasible, but still needs the complete API integration, long-text/format/
concurrency regressions, image size and memory measurements, and owner listening
acceptance before a production switch. The experimental probe is intentionally
separate; no all-PyTorch STT or NPU replacement is claimed here.
