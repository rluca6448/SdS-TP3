import argparse
import csv
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path


FU_PATTERN = re.compile(r"Fu\([^)]*\) = ([0-9.eE+-]+)")
T90_PATTERN = re.compile(r"t90 = ([0-9.eE+-]+)")


def create_animation(state_file, config, animation_dir, fps):
    animation_file = animation_dir / state_file.with_suffix(".gif").name
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("animate_states.py")),
            str(state_file),
            "--config", str(config),
            "--output", str(animation_file),
            "--fps", str(fps),
        ],
        check=True,
    )


def run_once(executable, config, output, tmax):
    start = time.perf_counter()
    result = subprocess.run(
        [str(executable), str(tmax), "100", str(config), str(output)],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    runtime = time.perf_counter() - start
    fu_match = FU_PATTERN.search(result.stdout)
    t90_match = T90_PATTERN.search(result.stdout)
    return runtime, float(fu_match.group(1)), (
        float(t90_match.group(1)) if t90_match else None
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("generated/competition"))
    parser.add_argument("--tmax", type=int, default=100)
    parser.add_argument(
        "--animate",
        action="store_true",
        help="genera un GIF por cada realizacion",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=1,
        help="cuadros por segundo de las animaciones",
    )
    args = parser.parse_args()

    if not args.config.exists():
        raise FileNotFoundError(args.config)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    animation_dir = args.output_dir / "animations"
    if args.animate:
        animation_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for replication in range(1, 6):
        output = args.output_dir / f"run{replication}.txt"
        runtime, fu, t90 = run_once(args.exe, args.config, output, args.tmax)
        rows.append({
            "replication": replication,
            "runtime_seconds": runtime,
            "fu_tmax": fu,
            "goals_tmax": fu * 100,
            "t90": t90,
            "state_file": output,
        })
        if args.animate:
            create_animation(output, args.config, animation_dir, args.fps)

    successful = [row for row in rows if row["t90"] is not None]
    unsuccessful = [row for row in rows if row["t90"] is None]
    ranking_key = (
        0, sum(row["t90"] for row in successful) / len(successful)
    ) if not unsuccessful else (
        1, -sum(row["goals_tmax"] for row in rows) / len(rows)
    )

    summary = args.output_dir / "competition.csv"
    with summary.open("w", newline="", encoding="utf-8") as summary_file:
        writer = csv.DictWriter(
            summary_file,
            fieldnames=[
                "replication", "runtime_seconds", "fu_tmax",
                "goals_tmax", "t90", "state_file",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"ranking_key = {ranking_key}")
    print(f"summary = {summary}")


if __name__ == "__main__":
    main()
