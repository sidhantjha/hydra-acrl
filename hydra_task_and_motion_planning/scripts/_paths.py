"""Shared input and output arguments for the standalone experiment scripts."""

import argparse
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]


def experiment_args(*, outputs=False, start=None, goal=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsg", required=True, type=Path, help="Input Spark-DSG JSON")
    if outputs:
        parser.add_argument("--output-dir", type=Path, help="Directory for generated outputs")
    if start is not None:
        parser.add_argument("--start", default=start, help="Start PLACES node ID")
    if goal is not None:
        parser.add_argument("--goal", default=goal, help="Goal PLACES node ID")
    args = parser.parse_args()
    args.dsg = args.dsg.expanduser().resolve()
    if not args.dsg.is_file():
        parser.error(f"DSG missing: {args.dsg}. Provide an approved graph with --dsg.")
    if outputs and args.output_dir is not None:
        args.output_dir = args.output_dir.expanduser().resolve()
    return args


def output_path(directory, filename):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    if path.exists() or path.is_symlink():
        raise SystemExit(f"Output exists: {path}. Use a new --output-dir.")
    return path
