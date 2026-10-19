from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Map Beaconcrest source data into the Nevis canonical model")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="Run the complete mapping pipeline")
    run.add_argument("--sources", type=Path, default=Path("sources"))
    run.add_argument("--output", type=Path, default=Path("outputs"))
    run.add_argument("--mode", choices=("replay", "real"), default="replay")
    run.add_argument("--model", default=None)
    run.add_argument("--confidence-threshold", type=float, default=0.90)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = run_pipeline(args.sources, args.output, args.mode, args.model, args.confidence_threshold)
    print(json.dumps({
        "source_counts": result["source_counts"],
        "entity_counts": result["canonical"]["validation_summary"]["entity_counts"],
        "hard_errors": result["canonical"]["validation_summary"]["hard_errors"],
        "llm_mode": result["manifest"]["mode"],
        "real_llm_used": result["manifest"]["real_llm_used"],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
