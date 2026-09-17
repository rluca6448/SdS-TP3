import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command, cwd=ROOT):
    print("$", " ".join(str(part) for part in command))
    subprocess.run(command, cwd=cwd, check=True)


def python_script(name):
    return [sys.executable, str(ROOT / "scripts" / name)]


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta el flujo experimental completo del TP3"
    )
    parser.add_argument(
        "--exe",
        type=Path,
        default=ROOT / "build" / "sds_tp3",
        help="ruta al ejecutable C++",
    )
    parser.add_argument(
        "--obstacle-config",
        type=Path,
        default=ROOT / "generated" / "obstacles.txt",
        help="configuracion final de obstaculos",
    )
    parser.add_argument(
        "--n-values",
        nargs="+",
        type=int,
        default=[25, 50, 100, 200],
        help="valores de N para el punto 1.1",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "generated" / "tp_results",
    )
    parser.add_argument(
        "--skip-competition",
        action="store_true",
        help="omite las cinco realizaciones de competencia",
    )
    args = parser.parse_args()

    executable = args.exe if args.exe.is_absolute() else ROOT / args.exe
    obstacle_config = (
        args.obstacle_config
        if args.obstacle_config.is_absolute()
        else ROOT / args.obstacle_config
    )
    output_dir = (
        args.output_dir
        if args.output_dir.is_absolute()
        else ROOT / args.output_dir
    )

    if not executable.exists():
        raise FileNotFoundError(
            f"No se encontro el ejecutable: {executable}. "
            "Compilalo antes de ejecutar el pipeline."
        )

    generated_dir = ROOT / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    obstacle_config.parent.mkdir(parents=True, exist_ok=True)

    empty_config = generated_dir / "mesa_vacia.txt"
    empty_config.touch()

    if not obstacle_config.exists():
        print("No existe la configuracion final; se genera una configuracion valida.")
        run([str(executable), "0", "100", str(obstacle_config),
             str(generated_dir / "configuration_init.txt")])

    run(python_script("validate_config.py") + [str(obstacle_config)])
    run(python_script("validate_config.py") + [str(empty_config)])

    point_11_dir = output_dir / "point_1_1"
    point_12_dir = output_dir / "point_1_2"
    point_11_dir.mkdir(parents=True, exist_ok=True)
    point_12_dir.mkdir(parents=True, exist_ok=True)

    run(
        python_script("run_experiments.py")
        + [
            "--exe", str(executable),
            "--config", str(empty_config),
            "--n-values", *[str(value) for value in args.n_values],
            "--repetitions", "10",
            "--tmax", "30",
            "--output-dir", str(point_11_dir),
        ]
    )
    run(
        python_script("analyze_experiments.py")
        + [str(point_11_dir / "results.csv"),
           "--output-dir", str(point_11_dir)]
    )

    run(
        python_script("run_experiments.py")
        + [
            "--exe", str(executable),
            "--config", str(empty_config), str(obstacle_config),
            "--n-values", "100",
            "--repetitions", "5",
            "--tmax", "100",
            "--output-dir", str(point_12_dir),
        ]
    )
    run(
        python_script("analyze_experiments.py")
        + [str(point_12_dir / "results.csv"),
           "--output-dir", str(point_12_dir),
           "--diffusion-n", "100"]
    )

    if not args.skip_competition:
        run(
            python_script("run_competition.py")
            + [
                "--exe", str(executable),
                "--config", str(obstacle_config),
                "--output-dir", str(output_dir / "competition"),
            ]
        )

    print()
    print("Pipeline terminado.")
    print(f"Resultados: {output_dir}")
    print(f"Punto 1.1: {point_11_dir}")
    print(f"Punto 1.2/1.3: {point_12_dir}")
    if not args.skip_competition:
        print(f"Competencia: {output_dir / 'competition'}")


if __name__ == "__main__":
    main()
