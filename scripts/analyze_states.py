import argparse
import csv
from pathlib import Path


def read_states(path):
    frames = []
    with path.open(encoding="utf-8") as states_file:
        lines = [line.strip() for line in states_file]

    index = 0
    while index < len(lines):
        if not lines[index]:
            index += 1
            continue

        time = float(lines[index])
        index += 1
        particles = []
        while index < len(lines) and lines[index]:
            values = lines[index].split()
            if len(values) != 5:
                raise ValueError(f"Estado invalido en {path}: {lines[index]}")
            particles.append((float(values[0]), float(values[1])))
            index += 1
        frames.append((time, particles))

    if not frames:
        raise ValueError(f"El archivo no contiene estados: {path}")
    return frames


def calculate_msd(frames):
    initial_positions = frames[0][1]
    result = []
    for time, particles in frames:
        if len(particles) != len(initial_positions):
            raise ValueError("La cantidad de particulas cambia entre estados")
        squared_displacements = [
            (x - x0) ** 2 + (y - y0) ** 2
            for (x, y), (x0, y0) in zip(particles, initial_positions)
        ]
        result.append((time, sum(squared_displacements) / len(squared_displacements)))
    return result


def linear_fit(points):
    mean_x = sum(x for x, _ in points) / len(points)
    mean_y = sum(y for _, y in points) / len(points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    if denominator == 0:
        raise ValueError("No se puede ajustar el DCM con tiempos iguales")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator
    intercept = mean_y - slope * mean_x
    return slope, intercept


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("states", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fit-start", type=float, default=None)
    parser.add_argument("--fit-end", type=float, default=None)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()

    msd = calculate_msd(read_states(args.states))
    fit_points = [
        point for point in msd
        if (args.fit_start is None or point[0] >= args.fit_start)
        and (args.fit_end is None or point[0] <= args.fit_end)
    ]
    if len(fit_points) < 2:
        raise ValueError("Se necesitan al menos dos puntos para ajustar el DCM")

    slope, intercept = linear_fit(fit_points)
    diffusion = slope / 4.0

    output = args.output or args.states.with_name(f"{args.states.stem}_msd.csv")
    with output.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["time", "msd"])
        writer.writerows(msd)

    if args.plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError as error:
            raise SystemExit(
                "Para graficar se requiere matplotlib: pip install matplotlib"
            ) from error

        x_values = [time for time, _ in msd]
        y_values = [value for _, value in msd]
        fit_x = [time for time, _ in fit_points]
        fit_y = [slope * time + intercept for time in fit_x]

        plt.figure()
        plt.plot(x_values, y_values, "o", markersize=3, label="DCM")
        plt.plot(fit_x, fit_y, "-", label=f"Ajuste: D={diffusion:.6g}")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("DCM (m²)")
        plt.title("Desplazamiento cuadrático medio")
        plt.legend()
        plt.tight_layout()
        plot_path = output.with_suffix(".png")
        plt.savefig(plot_path, dpi=200)
        plt.close()
        print(f"plot = {plot_path}")

    print(f"D = {diffusion}")
    print(f"fit_slope = {slope}")
    print(f"fit_intercept = {intercept}")
    print(f"output = {output}")


if __name__ == "__main__":
    main()
