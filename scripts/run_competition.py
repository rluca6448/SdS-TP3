import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIGURATION_PATTERN = re.compile(r"obstacles(\d+)\.txt$")
FU_PATTERN = re.compile(r"Fu\([^)]*\) = ([0-9.eE+-]+)")
T90_PATTERN = re.compile(r"t90 = ([0-9.eE+-]+)")
INITIALIZATION_RETRIES = 5


def count_obstacles(config):
    with config.open(encoding="utf-8") as config_file:
        return sum(1 for line in config_file if line.strip())


def configuration_files(configurations_dir):
    configurations = sorted(
        (
            path for path in configurations_dir.glob("obstacles*.txt")
            if path.is_file() and CONFIGURATION_PATTERN.fullmatch(path.name)
        ),
        key=lambda path: int(CONFIGURATION_PATTERN.fullmatch(path.name).group(1)),
    )
    if not configurations:
        raise FileNotFoundError(
            f"No se encontraron configuraciones en {configurations_dir}"
        )
    return configurations


def generate_config(executable, configurations_dir, obstacle_count):
    configurations_dir.mkdir(parents=True, exist_ok=True)
    numbers = [
        int(CONFIGURATION_PATTERN.fullmatch(path.name).group(1))
        for path in configurations_dir.glob("obstacles*.txt")
        if CONFIGURATION_PATTERN.fullmatch(path.name)
    ]
    next_number = max(numbers, default=0) + 1
    config = configurations_dir / f"obstacles{next_number}.txt"
    initialization_file = configurations_dir / f"configuration_init{next_number}.txt"
    subprocess.run(
        [
            str(executable),
            "0",
            "100",
            str(config),
            str(initialization_file),
            str(obstacle_count),
        ],
        check=True,
    )
    generated_count = count_obstacles(config)
    if generated_count != obstacle_count:
        raise RuntimeError(
            "El ejecutable genero una cantidad inesperada de obstaculos: "
            f"se esperaban {obstacle_count}, pero genero {generated_count}."
        )
    print(f"configuracion generada: {config}")
    return config


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
    command = [str(executable), str(tmax), "100", str(config), str(output)]
    start = time.perf_counter()
    for attempt in range(1, INITIALIZATION_RETRIES + 1):
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            break
        except subprocess.CalledProcessError:
            output.unlink(missing_ok=True)
            if attempt == INITIALIZATION_RETRIES:
                raise
            print(
                f"Reintentando {config.name} corrida "
                f"({attempt}/{INITIALIZATION_RETRIES - 1})"
            )
    runtime = time.perf_counter() - start
    fu_match = FU_PATTERN.search(result.stdout)
    t90_match = T90_PATTERN.search(result.stdout)
    return runtime, float(fu_match.group(1)), (
        float(t90_match.group(1)) if t90_match else None
    )


def run_configuration(executable, config, output_dir, tmax, animate, fps):
    output_dir.mkdir(parents=True, exist_ok=True)
    animation_dir = output_dir / "animations"
    if animate:
        animation_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for replication in range(1, 6):
        output = output_dir / f"run{replication}.txt"
        runtime, fu, t90 = run_once(executable, config, output, tmax)
        rows.append({
            "replication": replication,
            "runtime_seconds": runtime,
            "fu_tmax": fu,
            "goals_tmax": fu * 100,
            "t90": t90,
            "state_file": output,
        })
        if animate:
            create_animation(output, config, animation_dir, fps)

    successful = [row for row in rows if row["t90"] is not None]
    unsuccessful = [row for row in rows if row["t90"] is None]
    ranking_key = (
        0, sum(row["t90"] for row in successful) / len(successful)
    ) if not unsuccessful else (
        1, -sum(row["goals_tmax"] for row in rows) / len(rows)
    )

    summary = output_dir / "competition.csv"
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
    print(f"{config.name}: ranking_key = {ranking_key}")
    print(f"{config.name}: summary = {summary}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument(
        "--configurations-dir",
        type=Path,
        default=ROOT / "generated" / "configurations",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "generated" / "competition",
    )
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
    parser.add_argument(
        "--new-obstacles",
        nargs="?",
        const=3,
        type=int,
        default=None,
        metavar="CANTIDAD",
        help="genera una nueva configuracion antes de las corridas",
    )
    args = parser.parse_args()

    args.exe = args.exe.resolve()
    args.configurations_dir = args.configurations_dir.resolve()
    args.output_dir = args.output_dir.resolve()

    if args.new_obstacles is not None and args.new_obstacles <= 0:
        raise ValueError("La cantidad de obstaculos debe ser positiva")

    if args.new_obstacles is not None:
        generate_config(args.exe, args.configurations_dir, args.new_obstacles)
    configurations = configuration_files(args.configurations_dir)
    for config in configurations:
        match = CONFIGURATION_PATTERN.fullmatch(config.name)
        config_number = int(match.group(1))
        run_configuration(
            args.exe,
            config,
            args.output_dir / f"config{config_number}",
            args.tmax,
            args.animate,
            args.fps,
        )


if __name__ == "__main__":
    main()
