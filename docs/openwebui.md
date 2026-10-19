# OpenWebUI audio integration

Keep OpenWebUI and its chat/LLM provider independently configured. This server
handles speech only and does not replace your LLM or document embeddings.

1. Verify the speech `/health` endpoint and run scripts/smoke.py first.
2. In OpenWebUI's administrator Audio settings choose the OpenAI-compatible
   speech provider. Use `http://YOUR_SPEECH_HOST:8880/v1` as the base URL.
   If OpenWebUI is another container, its localhost is not the Docker host.
   Use a reachable host bind address or shared Docker service DNS on an explicitly
   joined trusted network. Do not publish the internal STT worker.
3. TTS model: `kokoro-82m-xpu`; voice: `af_sky`; request MP3 or WAV.
4. STT model: `whisper-large-v3-turbo-openvino`; set the same private API key
   configured in SPEECH_API_KEY if you enabled authentication.
5. Leave the STT language empty for automatic detection or explicitly choose
   en/ru/uk where appropriate. The proxy forwards it; it does not silently force
   English. English is still the only enabled TTS voice in this reference.
6. Use a trusted HTTPS origin for the browser UI and allow microphone access.
   Test recognition/read-aloud with natural speech; synthetic backend tests do
   not exercise browser capture, silence detection or playback.

Exact Audio setting labels vary by WebUI version. Use the server's /docs OpenAPI
schema on your trusted local endpoint for API details. Keep chat history/RAG
volumes persistent when redeploying WebUI; this speech repository never manages them.
