import argparse
import csv
import os
import re
import subprocess
import sys
import time
from pathlib import Path


FU_PATTERN = re.compile(r"Fu\([^)]*\) = ([0-9.eE+-]+)")
T90_PATTERN = re.compile(r"t90 = ([0-9.eE+-]+)")
INITIALIZATION_RETRIES = 5
MAX_PARALLEL_ANIMATIONS = os.cpu_count() or 4


def parse_result(stdout):
    fu_match = FU_PATTERN.search(stdout)
    t90_match = T90_PATTERN.search(stdout)
    return (
        float(fu_match.group(1)) if fu_match else None,
        float(t90_match.group(1)) if t90_match else None,
    )


def start_animation(state_file, config, animation_dir, fps):
    animation_file = animation_dir / state_file.with_suffix(".gif").name
    process = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).with_name("animate_states.py")),
            str(state_file),
            "--config", str(config),
            "--output", str(animation_file),
            "--fps", str(fps),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process, state_file


def _reap(pending, finished):
    for process, state_file in finished:
        _, stderr = process.communicate()
        if process.returncode != 0:
            print(
                f"\nError generando animacion para {state_file.name}:\n{stderr}",
                file=sys.stderr,
            )
        pending.remove((process, state_file))


def wait_for_slot(pending, max_parallel):
    while len(pending) >= max_parallel:
        finished = [item for item in pending if item[0].poll() is not None]
        if not finished:
            time.sleep(0.2)
            continue
        _reap(pending, finished)


def wait_for_all_animations(pending):
    total = len(pending)
    if total == 0:
        return
    completed = 0
    print(f"Generando animaciones... (0/{total})", end="\r", flush=True)
    while pending:
        finished = [item for item in pending if item[0].poll() is not None]
        if not finished:
            time.sleep(0.2)
            continue
        completed += len(finished)
        _reap(pending, finished)
        print(f"Generando animaciones... ({completed}/{total})", end="\r", flush=True)
    print(f"Animaciones listas ({total}/{total})" + " " * 10)


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

    pending_animations = []

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
                    for attempt in range(1, INITIALIZATION_RETRIES + 1):
                        try:
                            completed = subprocess.run(
                                command,
                                stdout=subprocess.PIPE,
                                text=True,
                                check=True,
                            )
                            break
                        except subprocess.CalledProcessError:
                            state_file.unlink(missing_ok=True)
                            if attempt == INITIALIZATION_RETRIES:
                                raise
                            print(
                                f"Reintentando {config.stem} N={particle_count} "
                                f"corrida={replication} "
                                f"({attempt}/{INITIALIZATION_RETRIES - 1})"
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
                        wait_for_slot(pending_animations, MAX_PARALLEL_ANIMATIONS)
                        pending_animations.append(
                            start_animation(state_file, config, animation_dir, args.fps)
                        )

    wait_for_all_animations(pending_animations)


if __name__ == "__main__":
    main()