# Troubleshooting and limits

- No XPU or wrong GPU: check host support, actual DRM mapping, group IDs and
  selectors. Verify both health device names; PyTorch and OpenVINO device
  numbering need not match. This project has measured only Arc Pro B50.
- Long utterance repeat/scatter failures: the build applies a narrow Kokoro0.9.4
  alignment workaround. A small duration/alignment construction runs on CPU;
  neural layers remain on XPU. Exact source occurrences are asserted. If a later
  Kokoro changes them, review the code rather than deleting the assertion.
- Do not confuse earlier ONNX/OpenVINO Kokoro failures with the working native
  PyTorch path. This project uses native Kokoro weights for TTS.
- Slow first reply: distinguish startup load, first inference/compile and warm
  inference. Model workers remain loaded for interactive latency; their memory
  is not automatically reclaimed after each utterance.
- Non-English STT: explicit language can help, but a supported language token
  does not prove accurate recognition on your accents/noise. English-only af_sky
  does not provide Russian/Ukrainian speech synthesis.
- Empty/unsupported input: TTS supports1-2000characters and speed0.5-2.0;
  STT supports25MiB/five-minute audio and JSON at the public proxy. This is not
  a streaming STT/TTS API or a realtime VAD implementation.
- Queue contention: each worker serializes its own model access, but TTS and STT
  may still share physical GPU scheduling with other processes. Do not claim
  speech tail latency from isolated warm medians.
- NPU: earlier host-specific experiments ran Whisper on NPU, but this repository
  does not publish an NPU driver/passthrough recipe or claim the Arc Docker
  device mappings enable NPU. Keep that experiment separate.
