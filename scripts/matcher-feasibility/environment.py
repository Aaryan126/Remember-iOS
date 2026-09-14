#!/usr/bin/env python3
"""Pin/download public model assets and record the isolated stage-1 environment.

Does not load a model, run inference, train, or modify global packages.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

from experiment import require, save, sha

MODEL = "microsoft/MiniLM-L12-H384-uncased"


def publish_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == data, f"existing artifact differs: {path}")
        return
    fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def verify_assets(workspace, manifest):
    directory = (workspace / manifest["workspaceRelativeDirectory"]).resolve()
    require(directory.is_relative_to(workspace.resolve()), "model directory escapes workspace")
    require(bool(manifest.get("assets")), "empty model asset manifest")
    for name, expected in manifest["assets"].items():
        path = (directory / name).resolve()
        require(path.is_relative_to(directory), "model asset escapes directory")
        require(path.is_file() and path.stat().st_size == expected["bytes"]
                and sha(path) == expected["sha256"], f"model asset mismatch: {name}")
    return len(manifest["assets"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true", help="offline, read-only check of installed packages and pinned assets")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    require(workspace.name == "v1" and workspace.parent.name == "RememberMatcherFeasibility",
            "expected dedicated RememberMatcherFeasibility/v1 workspace")
    require(workspace.is_dir(), "create the isolated venv first")
    require(shutil.disk_usage(workspace).free >= 10 * 1024**3, "less than 10GiB free")
    import requests
    import torch
    import transformers
    import sklearn
    import coremltools
    import numpy

    check = subprocess.run([os.sys.executable, "-m", "pip", "check"], capture_output=True, text=True, check=True)
    distributions = sorted((d.metadata["Name"].lower(), d.version) for d in importlib.metadata.distributions())
    lock = "# Resolved in isolated Python 3.11 macOS arm64 environment.\n" + "".join(f"{name}=={version}\n" for name, version in distributions)
    if args.verify_only:
        require((args.output / "environment.lock.txt").read_text() == lock, "installed environment differs from frozen lock")
        manifest = json.loads((args.output / "model-manifest.json").read_text())
        count = verify_assets(workspace, manifest)
        print(json.dumps({"verified": True, "assets": count, "packages": len(distributions),
                          "pipCheck": check.stdout.strip(), "mpsAvailable": torch.backends.mps.is_available(),
                          "freeBytes": shutil.disk_usage(workspace).free, "inferencePerformed": False}))
        return
    publish_bytes(args.output / "environment.lock.txt", lock.encode())

    # No auth, no model repository checkout, and no remote code execution.
    existing_manifest = args.output / "model-manifest.json"
    pinned = json.loads(existing_manifest.read_text())["revision"] if existing_manifest.exists() else None
    suffix = f"/revision/{pinned}" if pinned else ""
    response = requests.get(f"https://huggingface.co/api/models/{MODEL}{suffix}?blobs=true", timeout=60)
    response.raise_for_status()
    metadata = response.json()
    revision = metadata["sha"]
    require(re.fullmatch(r"[a-f0-9]{40}", revision), "invalid immutable model revision")
    asset_dir = workspace / "models" / revision
    required = {"config.json", "vocab.txt"}
    files = {row["rfilename"]: row for row in metadata["siblings"]}
    weights = "model.safetensors" if "model.safetensors" in files else "pytorch_model.bin"
    required.add(weights)
    require(required.issubset(files), "upstream model assets missing")
    selected = required | ({"tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "README.md", "LICENSE"} & set(files))
    assets = {}
    for name in sorted(selected):
        require(shutil.disk_usage(workspace).free >= 10 * 1024**3, "less than 10GiB free")
        path = asset_dir / name
        if not path.exists():
            print(f"Downloading public asset: {name}", flush=True)
            result = requests.get(f"https://huggingface.co/{MODEL}/resolve/{revision}/{name}", timeout=(30, 120))
            result.raise_for_status()
            # Verify against repository blob or LFS content hash before publication.
            data = result.content
            source = files[name]
            if "lfs" in source:
                require(hashlib.sha256(data).hexdigest() == source["lfs"]["sha256"], f"upstream content mismatch: {name}")
            elif source.get("blobId"):
                blob = b"blob " + str(len(data)).encode() + b"\0" + data
                require(hashlib.sha1(blob).hexdigest() == source["blobId"], f"upstream blob mismatch: {name}")
            publish_bytes(path, data)
        source = files[name]
        if "lfs" in source:
            require(sha(path) == source["lfs"]["sha256"], f"cached content mismatch: {name}")
        elif source.get("blobId"):
            data = path.read_bytes()
            require(hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == source["blobId"], f"cached blob mismatch: {name}")
        assets[name] = {"bytes": path.stat().st_size, "sha256": sha(path),
                        "url": f"https://huggingface.co/{MODEL}/resolve/{revision}/{name}"}
    config = json.loads((asset_dir / "config.json").read_text())
    require(config.get("hidden_size") == 384 and config.get("num_hidden_layers") == 12, "unexpected backbone architecture")
    manifest = {"schemaVersion": 1, "model": MODEL, "revision": revision,
                "license": metadata.get("cardData", {}).get("license", "unknown"),
                "assets": assets, "workspaceRelativeDirectory": f"models/{revision}",
                "loadPolicy": {"trustRemoteCode": False, "localFilesOnly": True,
                               "weightsOnly": True, "inferencePerformed": False},
                "architecture": {k: config.get(k) for k in ["model_type", "hidden_size", "num_hidden_layers", "vocab_size", "max_position_embeddings"]}}
    publish_bytes(args.output / "model-manifest.json", (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode())
    environment = {"schemaVersion": 1, "recordedAt": datetime.now(timezone.utc).isoformat(),
                   "python": platform.python_version(), "platform": platform.platform(), "machine": platform.machine(),
                   "versions": {"torch": torch.__version__, "transformers": transformers.__version__,
                                "coremltools": coremltools.__version__, "scikit-learn": sklearn.__version__, "numpy": numpy.__version__},
                   "mpsBuilt": torch.backends.mps.is_built(), "mpsAvailable": torch.backends.mps.is_available(),
                   "pipCheck": check.stdout.strip(), "freeBytesAfterSetup": shutil.disk_usage(workspace).free,
                   "modelBytes": sum(a["bytes"] for a in assets.values()), "stage2Started": False}
    save(args.output / "environment.json", environment)
    location = {"workspace": str(workspace), "python": os.sys.executable,
                "modelDirectory": str(asset_dir), "manifestSHA256": sha(args.output / "model-manifest.json")}
    publish_bytes(workspace / "location.json", (json.dumps(location, indent=2, ensure_ascii=False) + "\n").encode())
    print(json.dumps(environment, indent=2))


if __name__ == "__main__":
    main()
