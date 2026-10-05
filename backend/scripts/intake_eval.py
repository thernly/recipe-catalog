"""
Recipe cleanup eval harness (design doc §8). See app/services/intake_eval.py for the
eval-data layout.

Usage (from backend/):
    uv run python scripts/intake_eval.py draft              # cases for every input recipe
    uv run python scripts/intake_eval.py draft --sample 40  # a repeatable random sample
    uv run python scripts/intake_eval.py originals          # source record per case
    uv run python scripts/intake_eval.py run                # score checked cases
    uv run python scripts/intake_eval.py run --strict       # exit 1 below the targets

The folder defaults to backend/eval-data/ (git-ignored); override with --dir or
INTAKE_EVAL_DIR.
"""

import argparse
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.intake_eval import (  # noqa: E402
    DEFAULT_SAMPLE_SEED,
    draft_cases,
    eval_dir_from_env,
    format_report,
    run_eval,
    write_originals,
)


def _draft(eval_dir: Path, sample: int | None, seed: int) -> int:
    result = draft_cases(eval_dir, sample_size=sample, seed=seed)
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    print(
        f"Read {result.input_files} input file(s): {result.recipes_found} recipe(s)"
        + (f", sampled {result.sampled} (seed {seed})" if result.sampled is not None else "")
        + f", {result.already_drafted} already drafted."
    )
    print(f"Wrote {len(result.written)} draft case(s) to {eval_dir / 'cases'}")
    if len(result.written) <= 20:
        for path in result.written:
            print(f"  {path.name}")
    if result.written:
        print('Check each one, correct "expected", and set "checked": true.')
    return 0


def _originals(eval_dir: Path) -> int:
    result = write_originals(eval_dir)
    for problem in result.missing:
        print(f"Warning: {problem}", file=sys.stderr)
    print(f"Wrote {result.written} file(s) to {eval_dir / 'originals'}")
    if result.written:
        print("Each has the same name as its case in cases/.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["draft", "originals", "run"])
    parser.add_argument("--dir", type=Path, default=None, help="eval-data folder")
    parser.add_argument(
        "--sample", type=int, default=None, help="draft: only this many random recipes"
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SAMPLE_SEED, help="draft: seed for --sample"
    )
    parser.add_argument("--show", type=int, default=20, help="run: mismatches to print")
    parser.add_argument("--strict", action="store_true", help="run: exit 1 below targets")
    args = parser.parse_args()

    if args.sample is not None and args.sample < 1:
        parser.error("--sample must be at least 1")

    eval_dir = args.dir or eval_dir_from_env()
    if not eval_dir.exists():
        print(f"Eval folder not found: {eval_dir}", file=sys.stderr)
        return 2

    if args.command == "draft":
        return _draft(eval_dir, args.sample, args.seed)
    if args.command == "originals":
        return _originals(eval_dir)

    report = run_eval(eval_dir)
    print(format_report(report, show=args.show))
    if args.strict and not report.meets_targets():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
