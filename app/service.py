"""Local OpenAI-style API: B50 Kokoro XPU + isolated OpenVINO STT proxy.

Reference packaging of the measured B50 implementation; local-only by default.
"""

import io
import json
import os
import pathlib
import subprocess
import threading
import time
import wave
import contextlib
import numpy as np
import requests
import torch
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from validation import normalize_language, authorized, MAX_AUDIO_BYTES
from fastapi.responses import Response
from pydantic import BaseModel, Field
from kokoro import KModel, KPipeline

root = pathlib.Path(os.environ.get("MODEL_DIR", "/models"))
source = json.loads((root / "model-manifest.json").read_text())["kokoro"]
files = {
    name: str(root / "kokoro" / name)
    for name in ["config.json", "kokoro-v1_0.pth", "voices/af_sky.pt"]
}
device = os.environ.get("XPU_DEVICE", "xpu:0")
assert torch.xpu.is_available(), "Intel XPU is unavailable"
assert os.environ.get("EXPECTED_GPU_NAME", "Arc") in torch.xpu.get_device_name(
    device
), "Wrong XPU device"
torch.set_num_threads(6)
model = (
    KModel(
        repo_id=source["repo"],
        config=files["config.json"],
        model=files["kokoro-v1_0.pth"],
    )
    .to(device)
    .eval()
)
pipe = KPipeline(lang_code="a", repo_id=source["repo"], model=model)
pipe.voices["af_sky"] = torch.load(files["voices/af_sky.pt"], weights_only=True)
AMP = os.environ.get("TTS_AMP", "fp32")
assert AMP in ["fp32", "bf16"]
lock = threading.Lock()
app = FastAPI(title="Local B50 speech API")


@app.middleware("http")
async def api_auth(request, next):
    key = os.environ.get("SPEECH_API_KEY", "")
    if request.url.path != "/health" and not authorized(
        key, request.headers.get("authorization", "")
    ):
        return JSONResponse({"detail": "Authentication required"}, status_code=401)
    return await next(request)


STT = "whisper-large-v3-turbo-openvino"
TTS = "kokoro-82m-xpu"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "tts_device": str(model.device),
        "tts_device_name": torch.xpu.get_device_name(device),
        "stt_url": os.environ["STT_URL"],
        "precision": AMP,
        "torch": torch.__version__,
        "model_revision": source["revision"],
    }


@app.get("/v1/models")
def models():
    return {
        "object": "list",
        "data": [{"id": x, "object": "model"} for x in [STT, TTS]],
    }


@app.post("/v1/audio/transcriptions")
def transcribe(
    file: UploadFile = File(...),
    model: str = Form(STT),
    language: str = Form(""),
    response_format: str = Form("json"),
):
    if response_format != "json":
        raise HTTPException(422, "Transcription proxy supports JSON only")
    try:
        language = normalize_language(language)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    blob = file.file.read(MAX_AUDIO_BYTES + 1)
    if len(blob) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio limit25MiB")
    response = requests.post(
        os.environ["STT_URL"] + "/v1/audio/transcriptions",
        files={"file": (file.filename, blob, file.content_type)},
        data={"language": language, "response_format": "json"},
        timeout=180,
    )
    if not response.ok:
        raise HTTPException(502, "Intel STT backend failed")
    return response.json()


class Speech(BaseModel):
    model: str = TTS
    input: str = Field(min_length=1, max_length=2000)
    voice: str = "af_sky"
    response_format: str = "mp3"
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


@app.post("/v1/audio/speech")
def speech(body: Speech):
    if body.voice != "af_sky":
        raise HTTPException(422, "Only cached English af_sky is enabled")
    if body.response_format not in ["pcm", "wav", "mp3"]:
        raise HTTPException(422, "Supported formats: pcm, wav, mp3")
    started = time.perf_counter()
    with lock, torch.inference_mode(), (
        torch.autocast("xpu", dtype=torch.bfloat16)
        if AMP == "bf16"
        else contextlib.nullcontext()
    ):
        parts = [
            r.audio.float().numpy()
            for r in pipe(body.input, voice=body.voice, speed=body.speed)
        ]
        torch.xpu.synchronize(device)
    if not parts:
        raise HTTPException(422, "No pronounceable text")
    audio = np.concatenate(parts)
    if not np.isfinite(audio).all():
        raise HTTPException(500, "Nonfinite audio")
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes()
    headers = {
        "X-Synthesis-Seconds": str(time.perf_counter() - started),
        "X-Audio-Seconds": str(len(audio) / 24000),
    }
    if body.response_format == "pcm":
        return Response(pcm, media_type="audio/pcm", headers=headers)
    if body.response_format == "wav":
        out = io.BytesIO()
        with wave.open(out, "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(24000)
            f.writeframes(pcm)
        return Response(out.getvalue(), media_type="audio/wav", headers=headers)
    encoded = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "s16le",
            "-ar",
            "24000",
            "-ac",
            "1",
            "-i",
            "pipe:0",
            "-f",
            "mp3",
            "pipe:1",
        ],
        input=pcm,
        capture_output=True,
        timeout=60,
        check=True,
    )
    return Response(encoded.stdout, media_type="audio/mpeg", headers=headers)

