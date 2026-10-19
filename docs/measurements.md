# Recorded B50 speech measurements — October18,2026

These measurements describe the original measured implementation. Portable
packaging and HTTP client/auth changes are not a new performance benchmark.
Hardware: Intel Arc Pro B50,16GB. Torch2.14.0+xpu/Kokoro0.9.4 and matched
OpenVINO2026.5 nightly wheels; exact model revisions are in the setup guide.

| Workload | Warm median | Samples |
|---|---:|---:|
|Whisper,3.669s synthetic recording, greedy direct backend|0.108s|3|
|Whisper,10.112s synthetic recording, greedy direct backend|0.184s|3|
|Native Kokoro CPU,6.775s reply|1.240s|3|
|Native Kokoro B50 FP32, same reply|0.154s|3|
|Native Kokoro B50 BF16, same reply|0.120s|3|
|B50 FP32 TTS through HTTP API|0.156s|10|
|B50 BF16 TTS through HTTP API|0.122s|10|

FP32's first request took3.135seconds after1.899seconds of model/pipeline loading.
Warm results exclude that first inference. Peak Torch allocator observations
were about670MiB FP32 and627MiB BF16; these are not total card/driver memory
and exclude the separate OpenVINO worker and any concurrent workloads.

The native weights/phonemizer generated a different waveform/duration than an
older ONNX/P4 path. Do not interpret those cross-stack numbers as a controlled
GPU-only speedup. CPU versus XPU native Kokoro uses the same native path.
No T4 comparison or general Arc-card ranking is established here.

Inputs were synthetic speech, not a representative real-speaker/noise dataset.
These small-sample medians are neither a WER evaluation nor a production
tail-latency guarantee. Microphone capture, browser playback and human listening
are outside the timing boundary. English, Russian and Ukrainian natural-speech
acceptance and competing-workload behavior remain separate validation.

To reproduce locally, preserve the downloader manifest, image/package versions,
device names, prompts, recordings and API settings. Run one unscored warmup and
then repeated identical requests. Record both wall and X-Synthesis-Seconds /
X-Audio-Seconds headers, plus first-use behavior. The included smoke client is
an acceptance check, not a statistically complete benchmark harness.
