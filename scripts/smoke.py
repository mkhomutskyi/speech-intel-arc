"""Explicit TTS/STT round trip; generates a short synthetic clip, not a microphone test."""

import argparse
import json
import os
import pathlib
import time
import uuid
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8880")
    parser.add_argument(
        "--output", type=pathlib.Path, default=pathlib.Path("evidence/smoke")
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    headers = (
        {"Authorization": "Bearer " + os.environ["SPEECH_API_KEY"]}
        if os.environ.get("SPEECH_API_KEY")
        else {}
    )
    prompt = "The living room lights are on. I have set a timer for five minutes."
    request = urllib.request.Request(
        args.base_url + "/v1/audio/speech",
        data=json.dumps(
            {"input": prompt, "voice": "af_sky", "response_format": "wav"}
        ).encode(),
        headers={**headers, "Content-Type": "application/json"},
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=180) as response:
        wav = response.read()
        timings = {
            k: v for k, v in response.headers.items() if k.lower().startswith("x-")
        }
    tts_s = time.perf_counter() - start
    assert wav[:4] == b"RIFF" and wav[8:12] == b"WAVE"
    (args.output / "speech.wav").write_bytes(wav)
    boundary = "speech-" + uuid.uuid4().hex
    body = (
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="speech.wav"\r\nContent-Type: audio/wav\r\n\r\n'
        ).encode()
        + wav
        + (
            f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="language"\r\n\r\nen\r\n--{boundary}--\r\n'
        ).encode()
    )
    start = time.perf_counter()
    request = urllib.request.Request(
        args.base_url + "/v1/audio/transcriptions",
        data=body,
        headers={
            **headers,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        transcript = json.load(response)
    assert transcript.get("text")
    result = {
        "prompt": prompt,
        "transcript": transcript,
        "tts_wall_seconds": tts_s,
        "stt_wall_seconds": time.perf_counter() - start,
        "headers": timings,
        "scope": "Synthetic round trip; listen and test real recordings separately",
    }
    (args.output / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
