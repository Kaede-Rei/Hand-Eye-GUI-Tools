#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hand_eye_calibrator.ros.tf_reader import TfReader


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate that a TF transform is queryable."
    )
    parser.add_argument("parent")
    parser.add_argument("child")
    parser.add_argument("--timeout", type=float, default=0.5)
    args = parser.parse_args()
    T = TfReader().lookup(args.parent, args.child, args.timeout)
    print(T)


if __name__ == "__main__":
    main()
