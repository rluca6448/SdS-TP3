import argparse
import csv
import sys
from pathlib import Path

from analyze_experiments import (
    average_fu_curve_stats,
    calculate_fu_curve,
    create_diffusion_configuration_plot,
    create_fu_plot,
    state_path,
    write_configuration_plot,
)


def write_diffusion_plot(diffusion_paths, output):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omite el grafico")
        return

    points = []
    for diffusion_path in diffusion_paths:
        with diffusion_path.open(encoding="utf-8", newline="") as file:
            points.extend(csv.DictReader(file))

    valid = [
        row for row in points
        if row["t90_mean"] not in ("", "None")
    ]
    if not valid:
        output.unlink(missing_ok=True)
        return

    plt.figure(figsize=(max(7, len(valid) * 1.2), 5))
    colors = plt.cm.tab20(range(len(valid)))
    for color, row in zip(colors, valid):
        plt.errorbar(
            float(row["t90_mean"]),
            float(row["diffusion"]),
            xerr=(
                float(row.get("t90_std", 0.0))
                if row.get("t90_std", "") not in ("", "None")
                else 0.0
            ),
            fmt="none",
            ecolor=color,
            alpha=0.6,
        )
        plt.scatter(
            float(row["t90_mean"]),
            float(row["diffusion"]),
            color=color,
            label=(
                f"{Path(row['configuration']).stem} "
                f"(n={row.get('realization_count', '?')})"
            ),
            s=55,
        )
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("t90 promedio (s)")
    plt.ylabel("D")
    plt.title("Difusion vs t90 promedio")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()

    create_diffusion_configuration_plot(
        points,
        output.parent / "diffusion_by_configuration.png",
    )


def write_all_fu_plot(results_paths, output):
    curves_by_configuration = {}
    t90_by_configuration = {}
    for results_path in results_paths:
        with results_path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        for row in rows:
            configuration = row["configuration"]
            curves_by_configuration.setdefault(configuration, []).append(
                calculate_fu_curve(state_path(row["state_file"]))
            )
            if row["t90"] not in ("", "None"):
                t90_by_configuration.setdefault(configuration, []).append(
                    float(row["t90"])
                )
    curves = []
    for configuration, config_curves in sorted(
        curves_by_configuration.items()
    ):
        average_curve, std_curve = average_fu_curve_stats(config_curves)
        t90_values = t90_by_configuration.get(configuration, [])
        curves.append((
            f"{Path(configuration).stem} (n={len(config_curves)})",
            average_curve,
            std_curve,
            sum(t90_values) / len(t90_values) if t90_values else None,
            len(config_curves),
        ))
    create_fu_plot(
        curves,
        output,
        title="Fu(t) de todas las configuraciones",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Genera un unico grafico t90 para varias configuraciones"
    )
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    rows = []
    for summary in args.summaries:
        if not summary.exists():
            raise FileNotFoundError(summary)
        with summary.open(encoding="utf-8", newline="") as summary_file:
            rows.extend(csv.DictReader(summary_file))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_configuration_plot(rows, args.output)
    summary_dirs = [summary.parent for summary in args.summaries]
    write_diffusion_plot(
        [directory / "diffusion.csv" for directory in summary_dirs],
        args.output.parent / "diffusion_vs_t90.png",
    )
    write_all_fu_plot(
        [directory / "results.csv" for directory in summary_dirs],
        args.output.parent / "fu_vs_t.png",
    )
    print(f"configuration_plot = {args.output}")


if __name__ == "__main__":
    main()
