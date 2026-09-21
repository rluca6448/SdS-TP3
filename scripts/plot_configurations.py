import argparse
import csv
import sys
from pathlib import Path

from analyze_experiments import write_configuration_plot


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
    print(f"configuration_plot = {args.output}")


if __name__ == "__main__":
    main()
