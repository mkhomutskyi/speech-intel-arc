"""Experimental native OpenVINO Kokoro probe; does not modify the speech service."""

import argparse
import json
import os
import pathlib
import sys
import time
import wave

import numpy as np
import openvino as ov
import openvino_genai as genai


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--device", default="GPU")
    parser.add_argument("--expected-gpu", default="Arc")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument(
        "--text",
        default="The living room lights are on. I have set a timer for five minutes.",
    )
    args = parser.parse_args()
    assert args.repeats > 0
    args.output.mkdir(parents=True, exist_ok=False)
    name = ov.Core().get_property(args.device, "FULL_DEVICE_NAME")
    assert args.expected_gpu in name, name
    # The native frontend requires all four us/gb gold/silver lexicons.
    for dialect in ("us", "gb"):
        for tier in ("gold", "silver"):
            assert (args.model / "data" / f"{dialect}_{tier}.json").is_file()
    os.environ["MISAKI_DATA_DIR"] = str(args.model / "data")
    speaker = ov.Tensor(
        np.fromfile(args.model / "voices/af_sky.bin", dtype=np.float32).reshape(
            510, 1, 256
        )
    )
    started = time.perf_counter()
    pipeline = genai.Text2SpeechPipeline(str(args.model), args.device)
    result = {
        "device": name,
        "openvino": ov.__version__,
        "torch_imported": "torch" in sys.modules,
        "compile_seconds": time.perf_counter() - started,
        "text": args.text,
        "voice": "af_sky",
        "calls": [],
    }
    for index in range(args.repeats):
        started = time.perf_counter()
        decoded = pipeline.generate(args.text, speaker, language="en-us", speed=1.0)
        audio = np.concatenate(
            [np.asarray(tensor.data).reshape(-1) for tensor in decoded.speeches]
        )
        elapsed = time.perf_counter() - started
        assert len(audio) and np.isfinite(audio).all()
        rate = decoded.output_sample_rate
        result["calls"].append(
            {
                "wall_seconds": elapsed,
                "audio_seconds": len(audio) / rate,
                "real_time_factor": elapsed / (len(audio) / rate),
                "rms": float(np.sqrt(np.mean(audio * audio))),
            }
        )
        with wave.open(str(args.output / f"speech-{index}.wav"), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(
                (np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes()
            )
    (args.output / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
