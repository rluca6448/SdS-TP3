
import argparse
import math
from pathlib import Path


LENGTH = 1.20
WIDTH = 0.68
PARTICLE_RADIUS = 0.0175
GEOMETRY_EPSILON = 1e-12


def read_config(path):
    obstacles = []
    with path.open(encoding="utf-8") as config:
        for line_number, line in enumerate(config, start=1):
            if not line.strip():
                continue
            values = line.split()
            if len(values) != 3:
                raise ValueError(f"Linea {line_number}: se esperaban x, y, R")
            obstacles.append(tuple(map(float, values)))
    return obstacles


def validate(path):
    obstacles = read_config(path)
    for index, (x, y, radius) in enumerate(obstacles):
        if radius < PARTICLE_RADIUS:
            raise ValueError(f"Obstaculo {index}: R debe ser >= r")
        if not (
            radius - GEOMETRY_EPSILON
            <= x
            <= LENGTH - radius + GEOMETRY_EPSILON
        ):
            raise ValueError(f"Obstaculo {index}: excede el largo del tablero")
        if not (
            radius - GEOMETRY_EPSILON
            <= y
            <= WIDTH - radius + GEOMETRY_EPSILON
        ):
            raise ValueError(f"Obstaculo {index}: excede el ancho del tablero")
        for other_index, (other_x, other_y, other_radius) in enumerate(obstacles[:index]):
            distance = math.hypot(x - other_x, y - other_y)
            if distance < radius + other_radius - GEOMETRY_EPSILON:
                raise ValueError(
                    f"Obstaculos {other_index} y {index} se solapan"
                )
    return obstacles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    obstacles = validate(args.config)
    print(f"configuracion valida: {len(obstacles)} obstaculos")


if __name__ == "__main__":
    main()
