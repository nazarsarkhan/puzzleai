"""Print a stable summary of a puzzle reference archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from puzzle_pipeline.reference import inspect_reference


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_reference(args.archive), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
