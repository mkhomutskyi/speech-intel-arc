"""OpenVINO-only worker; isolate its GPU runtime from the Torch TTS process."""

import io
import os
import threading
import av
import numpy as np
import openvino as ov
import openvino_genai as genai
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from validation import normalize_language

core = ov.Core()
device = os.environ.get("OV_DEVICE", "GPU")
name = core.get_property(device, "FULL_DEVICE_NAME")
assert os.environ.get("EXPECTED_GPU_NAME", "Arc") in name, name
pipeline = genai.WhisperPipeline(
    os.environ.get("WHISPER_DIR", "/models/whisper"), device
)
lock = threading.Lock()
app = FastAPI(title="Arc B50 Whisper worker")


@app.get("/health")
def health():
    return {"status": "ok", "device": name, "openvino": ov.__version__, "num_beams": 1}


@app.post("/v1/audio/transcriptions")
def transcribe(
    file: UploadFile = File(...),
    language: str = Form(""),
    response_format: str = Form("json"),
):
    if response_format not in ["json", "text"]:
        raise HTTPException(422, "Use json or text")
    blob = file.file.read(25 * 1024 * 1024 + 1)
    if len(blob) > 25 * 1024 * 1024:
        raise HTTPException(413, "Audio limit 25 MiB")
    arrays = []
    resampler = av.AudioResampler(format="fltp", layout="mono", rate=16000)
    try:
        with av.open(io.BytesIO(blob)) as source:
            for frame in source.decode(audio=0):
                arrays.extend(
                    x.to_ndarray().reshape(-1) for x in resampler.resample(frame)
                )
            arrays.extend(x.to_ndarray().reshape(-1) for x in resampler.resample(None))
    except Exception:
        raise HTTPException(400, "Cannot decode audio")
    if not arrays:
        raise HTTPException(400, "Empty audio")
    samples = np.concatenate(arrays)
    if len(samples) > 16000 * 300:
        raise HTTPException(413, "Maximum duration five minutes")
    try:
        language = normalize_language(language)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    options = {"task": "transcribe", "max_new_tokens": 512, "num_beams": 1}
    if language:
        options["language"] = "<|" + language + "|>"
    with lock:
        result = pipeline.generate(samples, **options)
    text = " ".join(result.texts).strip()
    return (
        Response(text, media_type="text/plain")
        if response_format == "text"
        else {"text": text}
    )
