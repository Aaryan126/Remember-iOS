#!/usr/bin/env python3
"""Generate 36 local synthetic assets; do not read or record a user's media."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def run(args): subprocess.run([str(x) for x in args], check=True, stdout=subprocess.DEVNULL)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inputs", type=Path, default=Path("Evaluation/Organization/inputs-reviewed.json"))
    p.add_argument("--labels", type=Path, default=Path("Evaluation/Organization/labels.json"))
    p.add_argument("--freeze", type=Path, default=Path("Evaluation/Organization/freeze.json"))
    p.add_argument("--output", type=Path, default=Path("Evaluation/Organization/media"))
    args = p.parse_args()
    if args.output.exists(): raise ValueError("refusing to overwrite media release")
    frozen = json.loads(args.freeze.read_text())
    if frozen["inputsSHA256"] != sha(args.inputs) or frozen["labelsSHA256"] != sha(args.labels):
        raise ValueError("source corpus must match reviewed freeze")
    if not shutil.which("ffmpeg"): raise ValueError("ffmpeg required for synthetic WAV/video/scanned PDF fixtures")
    inputs, labels = json.loads(args.inputs.read_text()), json.loads(args.labels.read_text())
    labels = copy.deepcopy(labels)
    truths = {l["id"]: l for l in labels["libraries"]}
    generated, asset_manifest = [], []
    # Build in a fresh temporary directory; incomplete runs never masquerade as a release.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="remember-media-") as temporary:
        work = Path(temporary)
        release = work / "release"
        assets = release / "assets"
        assets.mkdir(parents=True)
        renderer = work / "render-fixture"
        run(["swiftc", "scripts/render_organization_fixture.swift", "-o", renderer])
        audio_count = video_count = pdf_count = 0
        for index, original in enumerate(inputs["libraries"]):
            library = copy.deepcopy(original)
            library["slice"] = "media"
            types = ["image", "pdf", "audio"] if index < 4 else (["image", "pdf", "video"] if index < 8 else ["image", "audio", "video"])
            for kind, position in zip(types, [2, 7, 14]):
                item = library["items"][position]
                text = item["text"]
                source = work / "source.txt"
                source.write_text(text)
                suffix = {"image": ".png", "pdf": ".pdf", "audio": ".wav", "video": ".mp4"}[kind]
                path = assets / (item["id"] + suffix)
                style = "degraded" if index % 2 else "clean"
                if kind == "image":
                    run([renderer, source, path, style, index])
                elif kind == "pdf":
                    pdf_count += 1
                    run([renderer, source, path, style, index])
                    # Alternate scanned PDFs by rasterizing then embedding a PNG in a PDF via Cocoa.
                    if pdf_count % 2 == 0:
                        png = assets / (item["id"] + "-scan.png")
                        run([renderer, source, png, "degraded", index])
                        run(["swift", "scripts/raster_organization_pdf.swift", png, path])
                        png.unlink()  # Only this newly generated intermediate; final PDF retained.
                elif kind == "audio":
                    audio_count += 1
                    aiff = work / "speech.aiff"
                    voice = "Mónica" if index == 10 else ("Thomas" if index == 11 else "Samantha")
                    run(["/usr/bin/say", "-v", voice, "-r", "165", "-f", source, "-o", aiff])
                    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", aiff]
                    if audio_count % 2 == 0:
                        command += ["-f", "lavfi", "-i", "anoisesrc=color=white:amplitude=0.015:sample_rate=16000:seed=1729",
                                    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:weights=1 0.2"]
                    run(command + ["-ar", "16000", "-ac", "1", path])
                else:
                    video_count += 1
                    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                         "testsrc2=size=320x240:rate=12", "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", path])
                    caption = text if video_count % 2 else ""
                    item["caption"] = caption
                    text = caption
                    if not caption:
                        truths[library["id"]]["memberships"][item["id"]] = ["unsupported-" + item["id"]]
                        truths[library["id"]].setdefault("rationale", {})[item["id"]] = "No caption; current video path has no semantic source evidence. Correct fallback is singleton."
                item.update(kind=kind, text=text, referenceText=text,
                            assetPath="assets/" + path.name, assetSHA256=sha(path))
                asset_manifest.append({"itemID": item["id"], "kind": kind, "sha256": sha(path),
                                       "style": style, "sourceFamily": original["id"], "split": library["split"]})
            # The controlled relationship slice checks shared-source links. Recompute
            # after removing unavailable video evidence rather than retaining stale edges.
            expected = truths[library["id"]]["memberships"]
            group_ids = sorted({g for groups in expected.values() for g in groups})
            relations = []
            for first, second in itertools.combinations(group_ids, 2):
                shared = [i for i, groups in expected.items() if first in groups and second in groups]
                evidence = shared or [next(i for i, groups in expected.items() if first in groups),
                                      next(i for i, groups in expected.items() if second in groups)]
                relations.append({"first": first, "second": second, "related": bool(shared), "evidence": evidence})
            truths[library["id"]]["relationships"] = relations
            generated.append(library)
        output = {"schemaVersion": 1, "libraries": generated}
        for name, value in [("inputs.json", output), ("labels.json", labels), ("assets.json", asset_manifest)]:
            (release / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        freeze = {"schemaVersion": 1, "inputsSHA256": sha(release / "inputs.json"), "labelsSHA256": sha(release / "labels.json"),
                  "parentFreezeSHA256": sha(args.freeze), "assetManifestSHA256": sha(release / "assets.json"),
                  "generatorSHA256": sha(Path(__file__)), "rendererSHA256": sha(Path("scripts/render_organization_fixture.swift")),
                  "scorerSHA256": sha(Path("scripts/organization_eval.py")), "contractSHA256": sha(Path("Evaluation/Organization/CONTRACT.md")),
                  "claim": "derived controlled media from agent-reviewed families; uncaptioned videos use prescribed singleton fallback; relationship slice is shared-source only"}
        (release / "freeze.json").write_text(json.dumps(freeze, indent=2) + "\n")
        shutil.copytree(release, args.output)
    print(json.dumps({"assets": len(asset_manifest), "libraries": len(generated), "output": str(args.output)}))


if __name__ == "__main__": main()
