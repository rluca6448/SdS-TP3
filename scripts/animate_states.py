import argparse
from pathlib import Path

LENGTH = 1.20
WIDTH = 0.68
GOAL_LENGTH = 0.20
PARTICLE_RADIUS = 0.0175


def read_animation_states(path):
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
                raise ValueError(f"Estado invalido: {lines[index]}")
            particles.append((
                float(values[0]),
                float(values[1]),
                int(values[4]),
            ))
            index += 1
        frames.append((time, particles))

    if not frames:
        raise ValueError(f"El archivo no contiene estados: {path}")
    return frames


def calculate_t90(frames):
    particle_count = len(frames[0][1])
    if particle_count == 0:
        return None
    for time, particles in frames:
        used_count = sum(state == 0 for _, _, state in particles)
        if used_count / particle_count >= 0.9:
            return time
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("states", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--fps",
        type=int,
        default=1,
        help="cuadros por segundo de reproduccion",
    )
    args = parser.parse_args()

    try:
        import matplotlib.animation as animation
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle, Rectangle
        from matplotlib.transforms import blended_transform_factory
    except ImportError as error:
        raise SystemExit(
            "Este script requiere matplotlib: pip install matplotlib"
        ) from error

    frames = read_animation_states(args.states)
    obstacles = []
    if args.config and args.config.exists():
        with args.config.open(encoding="utf-8") as config:
            for line in config:
                if line.strip():
                    obstacles.append(tuple(map(float, line.split())))

    figure, axes = plt.subplots()
    axes.set_aspect("equal")
    axes.set_xlim(0, LENGTH)
    axes.set_ylim(0, WIDTH)
    axes.set_xlabel("x (m)")
    axes.set_ylabel("y (m)")

    # Deja espacio arriba de los ejes para el titulo y las dos lineas de texto,
    # asi no se pisan entre si ni con el borde superior del tablero.
    figure.subplots_adjust(top=0.87)
    figure.suptitle("Billar-Metegol", y=0.97)

    # x queda anclado a los ejes (como antes, en 0.02) pero la altura se fija
    # en coordenadas de la figura, para que no dependa del aspect ratio de
    # los ejes ni se acerque al titulo o al borde del tablero.
    label_transform = blended_transform_factory(axes.transAxes, figure.transFigure)

    axes.add_patch(Rectangle((0, 0), LENGTH, WIDTH, fill=False, linewidth=2))
    axes.plot(
        [0, 0],
        [(WIDTH - GOAL_LENGTH) / 2, (WIDTH + GOAL_LENGTH) / 2],
        color="green",
        linewidth=5,
    )
    axes.plot(
        [LENGTH, LENGTH],
        [(WIDTH - GOAL_LENGTH) / 2, (WIDTH + GOAL_LENGTH) / 2],
        color="green",
        linewidth=5,
    )

    for x, y, radius in obstacles:
        axes.add_patch(Circle((x, y), radius, color="black"))

    particle_patches = [
        Circle((0, 0), PARTICLE_RADIUS, color="blue")
        for _ in frames[0][1]
    ]
    for patch in particle_patches:
        axes.add_patch(patch)

    time_label = figure.text(0.02, 0.90, "", transform=label_transform)
    last_used_count = sum(state == 0 for _, _, state in frames[0][1])
    t90 = calculate_t90(frames)
    final_label = (
        f"t90 = {t90:.6g} s" if t90 is not None else "t90 no alcanzado"
    )
    t90_label = figure.text(0.02, 0.845, final_label, transform=label_transform)

    def update(frame_index):
        nonlocal last_used_count
        time, particles = frames[frame_index]
        used_count = sum(state == 0 for _, _, state in particles)
        last_used_count = used_count
        for patch, (x, y, state) in zip(particle_patches, particles):
            patch.center = (x, y)
            patch.set_color("blue" if state == 1 else "red")
        time_label.set_text(
            f"t = {time:.6g} s | Ng = {used_count}/{len(particles)}"
        )
        return [*particle_patches, time_label, t90_label]

    rendered = animation.FuncAnimation(
        figure,
        update,
        frames=len(frames),
        interval=1000 / max(1, args.fps),
        blit=False,
    )

    if args.output:
        rendered.save(args.output, writer="pillow", fps=args.fps)
        print(final_label)
        print(f"animation = {args.output}")
    else:
        plt.show()
        print(final_label)


if __name__ == "__main__":
    main()