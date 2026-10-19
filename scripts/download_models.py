"""Download explicitly pinned public weights, verify hashes, write a portable manifest."""

import argparse
import hashlib
import json
import pathlib
import urllib.request

SOURCES = {
    "kokoro": ("hexgrad/Kokoro-82M", "f3ff3571791e39611d31c381e3a41a3af07b4987"),
    "whisper": (
        "OpenVINO/whisper-large-v3-turbo-fp16-ov",
        "0250c28d68c7c10d6b5cb39707e876c0c66ab6f8",
    ),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=pathlib.Path, default=pathlib.Path("data/models")
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for family, (repo, revision) in SOURCES.items():
        url = f"https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true"
        with urllib.request.urlopen(url, timeout=60) as response:
            info = json.load(response)
        assert info["sha"] == revision
        files = []
        for entry in info["siblings"]:
            name = entry["rfilename"]
            if family == "kokoro" and name not in [
                "config.json",
                "kokoro-v1_0.pth",
                "voices/af_sky.pt",
            ]:
                continue
            if family == "whisper" and not name.endswith(
                (".json", ".txt", ".xml", ".bin")
            ):
                continue
            relative = pathlib.PurePosixPath(name)
            assert not relative.is_absolute() and ".." not in relative.parts
            target = args.output / family / name
            target.parent.mkdir(parents=True, exist_ok=True)
            expected_hash = (entry.get("lfs") or {}).get("sha256")
            expected_size = entry.get("size") or (entry.get("lfs") or {}).get("size")
            valid = target.exists()
            if valid and expected_size is not None:
                valid = target.stat().st_size == expected_size
            if valid and expected_hash:
                with target.open("rb") as f:
                    valid = (
                        hashlib.file_digest(f, "sha256").hexdigest() == expected_hash
                    )
            if not valid:
                partial = target.with_name(target.name + ".part")
                request = f"https://huggingface.co/{repo}/resolve/{revision}/{name}"
                with urllib.request.urlopen(
                    request, timeout=180
                ) as response, partial.open("wb") as f:
                    while chunk := response.read(4 * 1024 * 1024):
                        f.write(chunk)
                if expected_size is not None:
                    assert partial.stat().st_size == expected_size, name
                if expected_hash:
                    with partial.open("rb") as f:
                        assert (
                            hashlib.file_digest(f, "sha256").hexdigest()
                            == expected_hash
                        ), name
                partial.replace(target)
            with target.open("rb") as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
            files.append(
                {"file": name, "bytes": target.stat().st_size, "sha256": digest}
            )
            print(f"Verified {family}/{name}", flush=True)
        assert files
        manifest[family] = {"repo": repo, "revision": revision, "files": files}
    (args.output / "model-manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
