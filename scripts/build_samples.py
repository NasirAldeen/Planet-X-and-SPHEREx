"""Rebuild the five real-observation showcase sequences from IRSA."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from planetx.archive import ROOT, build_sequence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="all")
    parser.add_argument("--limit", type=int, default=18)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    targets = json.loads((ROOT / "public/data/targets.json").read_text(encoding="utf-8"))
    failed = []
    for target in targets:
        if args.target not in ("all", target["id"]):
            continue
        print(f"\n{target['name']}", flush=True)
        try:
            result = build_sequence(target["ra"], target["dec"], target["fov"], target["detector"],
                                    args.limit, args.refresh, lambda s: print(s, flush=True))
            result["target"] = target
            path = ROOT / "public/data" / (target["id"] + ".json")
            path.write_text(json.dumps(result, separators=(",", ":"), allow_nan=False), encoding="utf-8")
            print(f"Saved {len(result['frames'])} real frames to {path.name}", flush=True)
        except Exception as exc:
            print(f"FAILED: {exc}", flush=True)
            failed.append(target["id"])
    if failed:
        raise SystemExit("Failed targets: " + ", ".join(failed))


if __name__ == "__main__":
    main()
