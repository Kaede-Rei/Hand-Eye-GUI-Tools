#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from piper_multicam_calibrator.core.io import read_data
from piper_multicam_calibrator.report.exporter import export_tf_bundle
from piper_multicam_calibrator.solvers.base import CalibrationResult
from piper_multicam_calibrator.core.transform import transform_from_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="Export static TF launch from result YAML files.")
    parser.add_argument("results", nargs="+")
    parser.add_argument("--output-root", default="./outputs")
    parser.add_argument("--project", default="c1_three_camera")
    args = parser.parse_args()
    results = []
    for path in args.results:
        payload = read_data(Path(path))
        results.append(
            CalibrationResult(
                payload["task_name"],
                payload["task_type"],
                payload["parent_frame"],
                payload["child_frame"],
                transform_from_dict(payload["T_parent_child"]),
                payload.get("sample_ids", []),
                payload.get("metrics", {}),
                payload.get("per_sample", []),
            )
        )
    out = export_tf_bundle(Path(args.output_root), args.project, results)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
