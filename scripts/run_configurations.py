import argparse
import csv
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev


ROOT = Path(__file__).resolve().parents[1]
FU_PATTERN = re.compile(r"Fu\([^)]*\) = ([0-9.eE+-]+)")
T90_PATTERN = re.compile(r"t90 = ([0-9.eE+-]+)")
INITIALIZATION_RETRIES = 5


def parse_result(stdout):
    fu_match = FU_PATTERN.search(stdout)
    t90_match = T90_PATTERN.search(stdout)
    if fu_match is None:
        raise RuntimeError("La simulacion no informo Fu(tmax)")
    return float(fu_match.group(1)), (
        float(t90_match.group(1)) if t90_match else None
    )


def validate_config(config):
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("validate_config.py")),
            str(config),
        ],
        check=True,
    )


def run_once(executable, config, state_file, tmax):
    start = time.perf_counter()
    command = [
        str(executable),
        str(tmax),
        "100",
        str(config),
        str(state_file),
    ]
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
                f"Reintentando {config.name} corrida "
                f"({attempt}/{INITIALIZATION_RETRIES - 1})"
            )
    runtime = time.perf_counter() - start
    fu_tmax, t90 = parse_result(completed.stdout)
    return runtime, fu_tmax, t90


def value_or_none(values):
    return mean(values) if values else None


def standard_deviation(values):
    return stdev(values) if len(values) >= 2 else 0.0


def configuration_name(config, configurations_dir):
    del configurations_dir
    return config.stem


def write_plot(summary_rows, output):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omite el grafico")
        return

    valid = [row for row in summary_rows if row["t90_mean"] is not None]
    if not valid:
        return

    labels = [row["configuration"] for row in valid]
    values = [row["t90_mean"] for row in valid]
    errors = [row["t90_std"] for row in valid]
    positions = list(range(len(labels)))

    plt.figure(figsize=(max(7, len(labels) * 1.2), 5))
    plt.errorbar(positions, values, yerr=errors, fmt="o", capsize=4)
    plt.xticks(positions, labels, rotation=30, ha="right")
    plt.ylabel("t90 promedio (s)")
    plt.title("Comparacion de configuraciones")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Ejecuta cinco realizaciones para cada archivo .txt encontrado "
            "en una carpeta de configuraciones"
        )
    )
    parser.add_argument(
        "--exe",
        type=Path,
        default=ROOT / "build" / "sds_tp3",
        help="ruta al ejecutable C++",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="directorio de resultados; por defecto, configurations/results",
    )
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--tmax", type=int, default=100)
    args = parser.parse_args()

    configurations_dir = ROOT / "generated" / "configurations"
    executable = args.exe if args.exe.is_absolute() else ROOT / args.exe
    output_dir = args.output_dir or configurations_dir / "results"
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    if not configurations_dir.is_dir():
        raise FileNotFoundError(
            f"No se encontro la carpeta de configuraciones: {configurations_dir}"
        )
    if not executable.exists():
        raise FileNotFoundError(f"No se encontro el ejecutable: {executable}")
    if args.repetitions <= 0:
        raise ValueError("repetitions debe ser positivo")
    if args.tmax <= 0:
        raise ValueError("tmax debe ser positivo")

    configs = sorted(
        (
            path for path in configurations_dir.glob("*.txt")
            if path.is_file() and not path.name.startswith("configuration_init")
        ),
    )
    if not configs:
        raise FileNotFoundError(
            f"No se encontraron archivos de configuracion en {configurations_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.csv"
    summary_path = output_dir / "summary.csv"
    plot_path = output_dir / "t90_by_configuration.png"
    rows = []

    for config in configs:
        validate_config(config)
        label = configuration_name(config, configurations_dir)

        for replication in range(1, args.repetitions + 1):
            state_file = output_dir / f"{config.stem}_run{replication}.txt"
            runtime, fu_tmax, t90 = run_once(
                executable, config, state_file, args.tmax
            )
            rows.append({
                "configuration": label,
                "config_file": str(config),
                "replication": replication,
                "N": 100,
                "tmax": args.tmax,
                "runtime_seconds": runtime,
                "fu_tmax": fu_tmax,
                "t90": t90,
                "state_file": str(state_file),
            })
            print(
                f"{label}: corrida {replication}/{args.repetitions}; "
                f"t90={t90}"
            )

    with results_path.open("w", newline="", encoding="utf-8") as results_file:
        fields = [
            "configuration", "config_file", "replication", "N", "tmax",
            "runtime_seconds", "fu_tmax", "t90", "state_file",
        ]
        writer = csv.DictWriter(results_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["configuration"]].append(row)

    summary_rows = []
    for label, config_rows in sorted(grouped.items()):
        t90_values = [
            row["t90"] for row in config_rows if row["t90"] is not None
        ]
        fu_values = [row["fu_tmax"] for row in config_rows]
        summary_rows.append({
            "configuration": label,
            "config_file": config_rows[0]["config_file"],
            "count": len(config_rows),
            "t90_count": len(t90_values),
            "t90_mean": value_or_none(t90_values),
            "t90_std": standard_deviation(t90_values),
            "fu_mean": mean(fu_values),
        })

    with summary_path.open("w", newline="", encoding="utf-8") as summary_file:
        fields = [
            "configuration", "config_file", "count", "t90_count",
            "t90_mean", "t90_std", "fu_mean",
        ]
        writer = csv.DictWriter(summary_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    successful = [
        row for row in summary_rows
        if row["t90_count"] == row["count"]
    ]
    if successful:
        best = min(successful, key=lambda row: row["t90_mean"])
    else:
        best = max(summary_rows, key=lambda row: row["fu_mean"])
    write_plot(summary_rows, plot_path)
    print(f"summary = {summary_path}")
    print(f"results = {results_path}")
    print(f"best_configuration = {best['configuration']}")
    print(f"best_config_file = {best['config_file']}")


if __name__ == "__main__":
    main()
