import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path


FU_PATTERN = re.compile(r"Fu\([^)]*\) = ([0-9.eE+-]+)")
T90_PATTERN = re.compile(r"t90 = ([0-9.eE+-]+)")


def parse_result(stdout):
    fu_match = FU_PATTERN.search(stdout)
    t90_match = T90_PATTERN.search(stdout)
    return (
        float(fu_match.group(1)) if fu_match else None,
        float(t90_match.group(1)) if t90_match else None,
    )


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--config", required=True, nargs="+", type=Path)
    parser.add_argument("--n-values", nargs="+", type=int, default=[100])
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--tmax", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, default=Path("generated/experiments"))
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

    if args.repetitions <= 0:
        raise ValueError("repetitions debe ser positivo")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    animation_dir = args.output_dir / "animations"
    if args.animate:
        animation_dir.mkdir(parents=True, exist_ok=True)
    results_path = args.output_dir / "results.csv"

    with results_path.open("w", newline="", encoding="utf-8") as results_file:
        fieldnames = [
            "configuration", "N", "replication", "tmax",
            "runtime_seconds", "fu_tmax", "t90", "state_file",
        ]
        writer = csv.DictWriter(results_file, fieldnames=fieldnames)
        writer.writeheader()

        for config in args.config:
            if not config.exists():
                raise FileNotFoundError(config)

            for particle_count in args.n_values:
                for replication in range(1, args.repetitions + 1):
                    state_file = (
                        args.output_dir
                        / f"{config.stem}_N{particle_count}_run{replication}.txt"
                    )
                    command = [
                        str(args.exe),
                        str(args.tmax),
                        str(particle_count),
                        str(config),
                        str(state_file),
                    ]

                    start = time.perf_counter()
                    completed = subprocess.run(
                        command,
                        stdout=subprocess.PIPE,
                        text=True,
                        check=True,
                    )
                    runtime = time.perf_counter() - start
                    fu_tmax, t90 = parse_result(completed.stdout)

                    writer.writerow({
                        "configuration": str(config),
                        "N": particle_count,
                        "replication": replication,
                        "tmax": args.tmax,
                        "runtime_seconds": runtime,
                        "fu_tmax": fu_tmax,
                        "t90": t90,
                        "state_file": str(state_file),
                    })
                    results_file.flush()
                    if args.animate:
                        create_animation(state_file, config, animation_dir, args.fps)


if __name__ == "__main__":
    main()
