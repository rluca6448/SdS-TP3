import argparse
import bisect
import csv
import math
import os
from collections import defaultdict
from pathlib import Path

from analyze_states import calculate_msd, linear_fit, read_states


def mean(values):
    return sum(values) / len(values) if values else None


def configuration_label(configuration):
    return Path(configuration).stem.replace("_", " ").replace("-", " ")


def state_path(value):
    path = Path(value)
    if path.exists() or os.name != "nt":
        return path
    text = str(value)
    if text.startswith("/mnt/") and len(text) > 7:
        windows_path = text[7:].replace("/", "\\")
        return Path(f"{text[5].upper()}:\\{windows_path}")
    return path


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


def calculate_fu_curve(path):
    curve = []
    frames = read_states(path)
    particle_count = len(frames[0][1])
    if particle_count == 0:
        return curve
    for time, particles in frames:
        if time <= 0:
            continue
        used_particles = sum(1 for particle in particles if particle[2] == 0)
        curve.append((time, used_particles / particle_count))
    return curve


def average_fu_curves(curves, point_count=80):
    valid_curves = [
        sorted((time, fu) for time, fu in curve if time > 0 and fu > 0)
        for curve in curves
    ]
    valid_curves = [curve for curve in valid_curves if curve]
    if not valid_curves:
        return []

    start = max(curve[0][0] for curve in valid_curves)
    end = min(curve[-1][0] for curve in valid_curves)
    if start >= end:
        return valid_curves[0]

    times = [
        start * (end / start) ** (index / (point_count - 1))
        for index in range(point_count)
    ]

    def interpolate(curve, time):
        curve_times = [point[0] for point in curve]
        right = bisect.bisect_left(curve_times, time)
        if right == 0:
            return curve[0][1]
        if right == len(curve):
            return curve[-1][1]
        left_time, left_value = curve[right - 1]
        right_time, right_value = curve[right]
        fraction = (time - left_time) / (right_time - left_time)
        return left_value + fraction * (right_value - left_value)

    return [
        (time, mean([interpolate(curve, time) for curve in valid_curves]))
        for time in times
    ]


def average_fu_curve_stats(curves, point_count=80):
    valid_curves = [
        sorted((time, fu) for time, fu in curve if time > 0 and fu > 0)
        for curve in curves
    ]
    valid_curves = [curve for curve in valid_curves if curve]
    if not valid_curves:
        return [], []

    start = max(curve[0][0] for curve in valid_curves)
    end = min(curve[-1][0] for curve in valid_curves)
    if start >= end:
        return valid_curves[0], [(time, 0.0) for time, _ in valid_curves[0]]

    times = [
        start * (end / start) ** (index / (point_count - 1))
        for index in range(point_count)
    ]

    def interpolate(curve, time):
        curve_times = [point[0] for point in curve]
        right = bisect.bisect_left(curve_times, time)
        if right == 0:
            return curve[0][1]
        if right == len(curve):
            return curve[-1][1]
        left_time, left_value = curve[right - 1]
        right_time, right_value = curve[right]
        fraction = (time - left_time) / (right_time - left_time)
        return left_value + fraction * (right_value - left_value)

    mean_curve = []
    std_curve = []
    for time in times:
        values = [interpolate(curve, time) for curve in valid_curves]
        mean_curve.append((time, mean(values)))
        std_curve.append((time, standard_deviation(values)))
    return mean_curve, std_curve


def write_fu_curve(path, output):
    curve = calculate_fu_curve(path)
    with output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["time", "fu"])
        writer.writerows(curve)
    return curve


def write_diffusion_and_correlation(rows, output, diffusion_n):
    by_configuration = defaultdict(list)
    for row in rows:
        if int(row["N"]) == diffusion_n:
            by_configuration[row["configuration"]].append(row)

    diffusion_rows = []
    for configuration, config_rows in sorted(by_configuration.items()):
        diffusion_values = []
        slope_values = []
        intercept_values = []
        for row in config_rows:
            diffusion, slope, intercept = calculate_diffusion(
                state_path(row["state_file"])
            )
            diffusion_values.append(diffusion)
            slope_values.append(slope)
            intercept_values.append(intercept)
        t90_values = [
            float(row["t90"]) for row in config_rows
            if row["t90"] not in ("", "None")
        ]
        diffusion_rows.append({
            "configuration": configuration,
            "diffusion": mean(diffusion_values),
            "diffusion_std": standard_deviation(diffusion_values),
            "fit_slope": mean(slope_values),
            "fit_intercept": mean(intercept_values),
            "t90_mean": mean(t90_values),
            "t90_std": standard_deviation(t90_values),
            "realization_count": len(config_rows),
        })

    with output.open("w", newline="", encoding="utf-8") as output_file:
        fields = [
            "configuration", "diffusion",
            "diffusion_std", "fit_slope", "fit_intercept",
            "t90_mean", "t90_std",
            "realization_count",
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
    return diffusion_rows


def create_msd_plot(state_file, output):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omite el grafico")
        return

    msd = calculate_msd(read_states(state_file))
    slope, intercept = linear_fit(msd)
    fit_x = [time for time, _ in msd]

    msd_positive = [(time, value) for time, value in msd
                    if time > 0 and value > 0]
    fit_positive = [(time, slope * time + intercept) for time in fit_x
                    if time > 0 and slope * time + intercept > 0]

    plt.figure()
    plt.plot([time for time, _ in msd_positive],
             [value for _, value in msd_positive], "o", markersize=3,
             label=r"$\langle z^2\rangle$")
    plt.plot(
        [time for time, _ in fit_positive],
        [value for _, value in fit_positive],
        "-",
        label=f"Ajuste lineal: D={slope / 4.0:.6g}",
    )
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Tiempo (s)")
    plt.ylabel(r"$\langle z^2\rangle$ (m$^2$)")
    plt.title(r"Desplazamiento cuadratico medio $\langle z^2\rangle$")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()


def create_diffusion_configuration_plot(diffusion_rows, output):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omite el grafico")
        return

    valid = [
        row for row in diffusion_rows
        if row["diffusion"] not in ("", "None")
    ]
    if not valid:
        output.unlink(missing_ok=True)
        return

    labels = [
        f"{configuration_label(row['configuration'])} "
        f"(n={row.get('realization_count', '?')})"
        for row in valid
    ]
    values = [float(row["diffusion"]) for row in valid]
    errors = [
        float(row.get("diffusion_std", 0.0) or 0.0)
        for row in valid
    ]
    colors = plt.cm.tab20(range(len(valid)))
    positions = list(range(len(labels)))

    plt.figure(figsize=(max(7, len(labels) * 1.2), 5))
    for position, value, error, color, label in zip(
        positions, values, errors, colors, labels
    ):
        plt.errorbar(
            position,
            value,
            yerr=error,
            fmt="o",
            color=color,
            capsize=4,
            label=label,
        )
    plt.xticks(positions, labels, rotation=30, ha="right")
    plt.ylabel("D")
    plt.title("Difusion por configuracion")
    plt.yscale("log")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()


def create_fu_plot(curves, output, title="Fu(t)"):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omite el grafico")
        return

    if not curves:
        output.unlink(missing_ok=True)
        return

    plt.figure()
    colors = plt.cm.tab20(range(len(curves)))
    for index, curve_data in enumerate(curves):
        label, curve, std_curve, t90, realization_count = curve_data
        color = colors[index]
        positive = [(time, fu) for time, fu in curve if time > 0 and fu > 0]
        if positive:
            plt.plot(
                [time for time, _ in positive],
                [fu for _, fu in positive],
                color=color,
                linewidth=1.8,
                label=label,
            )
            if std_curve:
                std_values = dict(std_curve)
                lower = [
                    max(1e-12, fu - std_values.get(time, 0.0))
                    for time, fu in positive
                ]
                upper = [
                    fu + std_values.get(time, 0.0)
                    for time, fu in positive
                ]
                plt.fill_between(
                    [time for time, _ in positive],
                    lower,
                    upper,
                    color=color,
                    alpha=0.15,
                )
        if t90 is not None and t90 > 0:
            plt.axvline(
                t90,
                color=color,
                linestyle=":",
                linewidth=1.2,
                alpha=0.9,
            )
    plt.xlabel("Tiempo (s)")
    plt.ylabel(r"$F_u(t)=N_g(t)/N$")
    plt.title(title)
    plt.xscale("log")
    plt.yscale("log")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()


def create_plots(grouped_path, diffusion_path, output_dir, rows):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omiten los graficos")
        return

    experiment_rows = rows
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
            label=(
                f"{configuration_label(configuration)} "
                f"(n={rows[0]['count']})"
            ),
        )
    plt.xlabel("N")
    plt.ylabel("Tiempo de ejecucion (s)")
    plt.xscale("log")
    plt.yscale("log")
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
                label=(
                    f"{configuration_label(configuration)} "
                    f"(n={valid[0]['count']})"
                ),
            )
        plt.xlabel("N")
        plt.ylabel("t90 promedio (s)")
        plt.xscale("log")
        plt.yscale("log")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "t90_vs_n.png")
        plt.close()
    else:
        (output_dir / "t90_vs_n.png").unlink(missing_ok=True)

    write_configuration_plot(grouped_rows, output_dir / "t90_by_configuration.png")

    diffusion_rows = list(csv.DictReader(diffusion_path.open(encoding="utf-8")))
    valid = [row for row in diffusion_rows if row["t90_mean"] not in ("", "None")]
    if valid:
        plt.figure()
        for row in valid:
            label = (
                f"{configuration_label(row['configuration'])} "
                f"(n={row.get('realization_count', '?')})"
            )
            plt.errorbar(
                float(row["t90_mean"]),
                float(row["diffusion"]),
                xerr=float(row.get("t90_std", 0.0)),
                fmt="o",
                capsize=3,
                label=label,
            )
        plt.xlabel("t90 promedio (s)")
        plt.ylabel("D")
        plt.xscale("log")
        plt.yscale("log")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "diffusion_vs_t90.png")
        plt.close()
    create_diffusion_configuration_plot(
        diffusion_rows,
        output_dir / "diffusion_by_configuration.png",
    )

    curves_by_configuration = defaultdict(list)
    t90_by_configuration = defaultdict(list)
    for row in experiment_rows:
        state_file = state_path(row["state_file"])
        curve_output = output_dir / f"{state_file.stem}_fu_vs_t.csv"
        curve = write_fu_curve(state_file, curve_output)
        curves_by_configuration[row["configuration"]].append(curve)
        if row["t90"] not in ("", "None"):
            t90_by_configuration[row["configuration"]].append(
                float(row["t90"])
            )
    curves = []
    for configuration, config_curves in sorted(
        curves_by_configuration.items()
    ):
        average_curve, std_curve = average_fu_curve_stats(config_curves)
        curves.append((
            f"{configuration_label(configuration)} "
            f"(n={len(config_curves)})",
            average_curve,
            std_curve,
            mean(t90_by_configuration[configuration]),
            len(config_curves),
        ))
    create_fu_plot(curves, output_dir / "fu_vs_t.png")

    state_files = [
        state_path(row["state_file"]) for row in experiment_rows
        if int(row["N"]) == min(int(item["N"]) for item in grouped_rows)
    ]
    if state_files:
        create_msd_plot(state_files[0], output_dir / "msd_vs_time.png")

    return diffusion_rows, curves


def write_configuration_plot(rows, output):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib no esta instalado; se omite el grafico")
        return

    by_configuration = defaultdict(list)
    for row in rows:
        if row["t90_mean"] not in ("", "None"):
            by_configuration[row["configuration"]].append(row)

    configuration_points = [
        (
            f"{configuration_label(configuration)} "
            f"(n={config_rows[0]['count']})",
            float(config_rows[0]["t90_mean"]),
            float(config_rows[0]["t90_std"]),
        )
        for configuration, config_rows in by_configuration.items()
        if len(config_rows) == 1
    ]

    if not configuration_points:
        output.unlink(missing_ok=True)
        return

    plt.figure(figsize=(max(7, len(configuration_points) * 1.2), 5))
    labels = [point[0] for point in configuration_points]
    values = [point[1] for point in configuration_points]
    errors = [point[2] for point in configuration_points]
    positions = list(range(len(labels)))
    plt.errorbar(positions, values, yerr=errors, fmt="o", capsize=4)
    plt.xticks(positions, labels, rotation=30, ha="right")
    plt.ylabel("t90 promedio (s)")
    plt.yscale("log")
    plt.title("Comparacion de configuraciones")
    plt.tight_layout()
    plt.savefig(output, dpi=200)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--diffusion-n", type=int, default=100)
    parser.add_argument(
        "--skip-configuration-plot",
        action="store_true",
        help="no genera el grafico t90_by_configuration en este directorio",
    )
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
    create_plots(grouped, diffusion, output_dir, rows)
    if args.skip_configuration_plot:
        (output_dir / "t90_by_configuration.png").unlink(missing_ok=True)
    print(f"summary = {grouped}")
    print(f"presentation_summary = {presentation}")
    print(f"diffusion = {diffusion}")


if __name__ == "__main__":
    main()
