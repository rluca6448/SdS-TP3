import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

from analyze_states import calculate_msd, linear_fit, read_states


def mean(values):
    return sum(values) / len(values) if values else None


def configuration_label(configuration):
    return Path(configuration).stem.replace("_", " ").replace("-", " ")


def standard_deviation(values):
    if len(values) < 2:
        return 0.0
    average = mean(values)
    return math.sqrt(
        sum((value - average) ** 2 for value in values) / (len(values) - 1)
    )


def write_grouped_results(rows, output):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["configuration"], int(row["N"]))].append(row)

    with output.open("w", newline="", encoding="utf-8") as output_file:
        fields = [
            "configuration", "N", "count",
            "runtime_mean", "runtime_std",
            "t90_count", "t90_mean", "t90_std",
            "fu_mean", "fu_std",
        ]
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()

        for (configuration, particle_count), group in sorted(groups.items()):
            runtimes = [float(row["runtime_seconds"]) for row in group]
            t90_values = [
                float(row["t90"]) for row in group
                if row["t90"] not in ("", "None")
            ]
            fu_values = [float(row["fu_tmax"]) for row in group]
            writer.writerow({
                "configuration": configuration,
                "N": particle_count,
                "count": len(group),
                "runtime_mean": mean(runtimes),
                "runtime_std": standard_deviation(runtimes),
                "t90_count": len(t90_values),
                "t90_mean": mean(t90_values),
                "t90_std": standard_deviation(t90_values),
                "fu_mean": mean(fu_values),
                "fu_std": standard_deviation(fu_values),
            })


def write_presentation_summary(rows, output):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["configuration"], int(row["N"]))].append(row)

    with output.open("w", encoding="utf-8") as summary_file:
        for (configuration, particle_count), group in sorted(groups.items()):
            runtimes = [float(row["runtime_seconds"]) for row in group]
            t90_values = [
                float(row["t90"]) for row in group
                if row["t90"] not in ("", "None")
            ]
            summary_file.write(
                f"configuration={configuration}; N={particle_count}; "
                f"realizations={len(group)}\n"
            )
            summary_file.write(
                f"runtime_mean={mean(runtimes)}; "
                f"runtime_std={standard_deviation(runtimes)}\n"
            )
            summary_file.write(
                f"t90_reached={len(t90_values)}/{len(group)}; "
                f"t90_mean={mean(t90_values)}; "
                f"t90_std={standard_deviation(t90_values)}\n\n"
            )


def calculate_diffusion(path):
    msd = calculate_msd(read_states(path))
    slope, intercept = linear_fit(msd)
    return slope / 4.0, slope, intercept


def write_diffusion_and_correlation(rows, output, diffusion_n):
    by_configuration = defaultdict(list)
    for row in rows:
        if int(row["N"]) == diffusion_n:
            by_configuration[row["configuration"]].append(row)

    diffusion_rows = []
    for configuration, config_rows in sorted(by_configuration.items()):
        state_file = Path(config_rows[0]["state_file"])
        diffusion, slope, intercept = calculate_diffusion(state_file)
        t90_values = [
            float(row["t90"]) for row in config_rows
            if row["t90"] not in ("", "None")
        ]
        diffusion_rows.append({
            "configuration": configuration,
            "diffusion": diffusion,
            "fit_slope": slope,
            "fit_intercept": intercept,
            "t90_mean": mean(t90_values),
        })

    with output.open("w", newline="", encoding="utf-8") as output_file:
        fields = [
            "configuration", "diffusion",
            "fit_slope", "fit_intercept", "t90_mean",
        ]
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(diffusion_rows)

    comparable = [
        row for row in diffusion_rows
        if row["t90_mean"] is not None
    ]
    if len(comparable) >= 2:
        x_mean = mean([row["t90_mean"] for row in comparable])
        y_mean = mean([row["diffusion"] for row in comparable])
        numerator = sum(
            (row["t90_mean"] - x_mean) * (row["diffusion"] - y_mean)
            for row in comparable
        )
        x_sum = sum((row["t90_mean"] - x_mean) ** 2 for row in comparable)
        y_sum = sum((row["diffusion"] - y_mean) ** 2 for row in comparable)
        correlation = (
            numerator / math.sqrt(x_sum * y_sum)
            if x_sum and y_sum else 0.0
        )
        print(f"correlation_t90_diffusion = {correlation}")


def create_plots(grouped_path, diffusion_path, output_dir):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omiten los graficos")
        return

    grouped_rows = list(csv.DictReader(grouped_path.open(encoding="utf-8")))
    by_configuration = defaultdict(list)
    for row in grouped_rows:
        by_configuration[row["configuration"]].append(row)

    plt.figure()
    for configuration, rows in by_configuration.items():
        rows.sort(key=lambda row: int(row["N"]))
        x = [int(row["N"]) for row in rows]
        y = [float(row["runtime_mean"]) for row in rows]
        error = [float(row["runtime_std"]) for row in rows]
        plt.errorbar(
            x, y, yerr=error, marker="o",
            label=configuration_label(configuration),
        )
    plt.xlabel("N")
    plt.ylabel("Tiempo de ejecucion (s)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "runtime_vs_n.png")
    plt.close()

    n_values = {
        int(row["N"])
        for rows in by_configuration.values()
        for row in rows
    }
    if len(n_values) > 1:
        plt.figure()
        for configuration, rows in by_configuration.items():
            valid = [
                row for row in rows
                if row["t90_mean"] not in ("", "None")
            ]
            if not valid:
                continue
            valid.sort(key=lambda row: int(row["N"]))
            x = [int(row["N"]) for row in valid]
            y = [float(row["t90_mean"]) for row in valid]
            error = [float(row["t90_std"]) for row in valid]
            plt.errorbar(
                x, y, yerr=error, marker="o",
                label=configuration_label(configuration),
            )
        plt.xlabel("N")
        plt.ylabel("t90 promedio (s)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "t90_vs_n.png")
        plt.close()
    else:
        (output_dir / "t90_vs_n.png").unlink(missing_ok=True)

    configuration_points = []
    for configuration, rows in by_configuration.items():
        valid = [row for row in rows if row["t90_mean"] not in ("", "None")]
        if len(valid) == 1:
            row = valid[0]
            configuration_points.append((
                configuration_label(configuration),
                float(row["t90_mean"]),
                float(row["t90_std"]),
            ))

    if configuration_points:
        plt.figure()
        labels = [point[0] for point in configuration_points]
        values = [point[1] for point in configuration_points]
        errors = [point[2] for point in configuration_points]
        positions = list(range(len(labels)))
        plt.errorbar(positions, values, yerr=errors, fmt="o")
        plt.xticks(positions, labels, rotation=30, ha="right")
        plt.ylabel("t90 promedio (s)")
        plt.title("Comparacion de configuraciones")
        plt.tight_layout()
        plt.savefig(output_dir / "t90_by_configuration.png", dpi=200)
        plt.close()

    diffusion_rows = list(csv.DictReader(diffusion_path.open(encoding="utf-8")))
    valid = [row for row in diffusion_rows if row["t90_mean"] not in ("", "None")]
    if valid:
        plt.figure()
        plt.scatter(
            [float(row["t90_mean"]) for row in valid],
            [float(row["diffusion"]) for row in valid],
        )
        plt.xlabel("t90 promedio (s)")
        plt.ylabel("D")
        plt.tight_layout()
        plt.savefig(output_dir / "diffusion_vs_t90.png")
        plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--diffusion-n", type=int, default=100)
    args = parser.parse_args()

    output_dir = args.output_dir or args.results.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(args.results.open(encoding="utf-8")))

    grouped = output_dir / "summary.csv"
    diffusion = output_dir / "diffusion.csv"
    presentation = output_dir / "presentation_summary.txt"
    write_grouped_results(rows, grouped)
    write_presentation_summary(rows, presentation)
    write_diffusion_and_correlation(rows, diffusion, args.diffusion_n)
    create_plots(grouped, diffusion, output_dir)
    print(f"summary = {grouped}")
    print(f"presentation_summary = {presentation}")
    print(f"diffusion = {diffusion}")


if __name__ == "__main__":
    main()
