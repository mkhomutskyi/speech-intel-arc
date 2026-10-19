"""Static publication checks; these do not emulate GPU inference."""

import ast
import json
import pathlib
import re
import yaml

root = pathlib.Path(".")
for p in root.rglob("*"):
    if ".git" in p.parts or ".pytest_cache" in p.parts:
        continue
    if p.suffix == ".json":
        json.loads(p.read_text(encoding="utf-8-sig"))
    if p.suffix in (".yml", ".yaml"):
        yaml.safe_load(p.read_text(encoding="utf-8-sig"))
    if p.suffix == ".py":
        ast.parse(p.read_text(encoding="utf-8-sig"))
    if p.suffix == ".md":
        for target in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8-sig")):
            if (
                "://" in target
                or target.startswith("#")
                or target.startswith("mailto:")
            ):
                continue
            assert (p.parent / target.split("#")[0]).exists(), (str(p), target)
print(
    "JSON, YAML, Python syntax and local Markdown links passed. GPU tests are separate."
)
