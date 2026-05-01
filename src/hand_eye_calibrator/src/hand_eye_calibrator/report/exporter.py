from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, TYPE_CHECKING

from hand_eye_calibrator.core.io import ensure_dir, write_data
from hand_eye_calibrator.core.transform import matrix_to_quaternion_xyzw

if TYPE_CHECKING:
    from hand_eye_calibrator.solvers.base import CalibrationResult


def _static_tf_node(result: CalibrationResult) -> str:
    T = result.T_parent_child
    x, y, z = [float(v) for v in T[:3, 3]]
    qx, qy, qz, qw = matrix_to_quaternion_xyzw(T[:3, :3])
    name = f"tf_{result.parent_frame}_to_{result.child_frame}".replace("/", "_")
    args = f"{x:.9g} {y:.9g} {z:.9g} {qx:.9g} {qy:.9g} {qz:.9g} {qw:.9g} {result.parent_frame} {result.child_frame}"
    return f'  <node pkg="tf2_ros" type="static_transform_publisher" name="{name}" args="{args}" />'


def export_result(output_root: Path, result: CalibrationResult) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ensure_dir(output_root / f"{result.task_name}_{stamp}")
    write_data(out / f"{result.task_name}.yaml", result.to_payload())
    (out / "report.md").write_text(_report_markdown([result]), encoding="utf-8")
    result.output_dir = str(out)
    return out


def export_tf_bundle(
    output_root: Path, project_name: str, results: Iterable[CalibrationResult]
) -> Path:
    results = list(results)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = ensure_dir(output_root / f"{project_name}_tf_{stamp}")
    write_data(out / "tf_tree.yaml", {"transforms": [r.to_payload() for r in results]})
    launch = ["<launch>", *[_static_tf_node(r) for r in results], "</launch>", ""]
    (out / "static_tf.launch").write_text("\n".join(launch), encoding="utf-8")
    sh_lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    for r in results:
        T = r.T_parent_child
        x, y, z = [float(v) for v in T[:3, 3]]
        qx, qy, qz, qw = matrix_to_quaternion_xyzw(T[:3, :3])
        sh_lines.append(
            "rosrun tf2_ros static_transform_publisher "
            f"{x:.9g} {y:.9g} {z:.9g} {qx:.9g} {qy:.9g} {qz:.9g} {qw:.9g} {r.parent_frame} {r.child_frame} &"
        )
    sh_lines.append("wait")
    (out / "static_tf.sh").write_text("\n".join(sh_lines) + "\n", encoding="utf-8")
    (out / "report.md").write_text(_report_markdown(results), encoding="utf-8")
    return out


def _report_markdown(results) -> str:
    lines = ["# Hand-Eye Calibration Report", ""]
    for r in results:
        t = r.T_parent_child[:3, 3]
        q = matrix_to_quaternion_xyzw(r.T_parent_child[:3, :3])
        lines.extend(
            [
                f"## {r.task_name}",
                "",
                f"- type: `{r.task_type}`",
                f"- tf: `{r.parent_frame}` -> `{r.child_frame}`",
                f"- samples: {len(r.sample_ids)}",
                f"- translation_m: [{t[0]:.9g}, {t[1]:.9g}, {t[2]:.9g}]",
                f"- rotation_xyzw: [{q[0]:.9g}, {q[1]:.9g}, {q[2]:.9g}, {q[3]:.9g}]",
                f"- metrics: `{r.metrics}`",
                "",
            ]
        )
    return "\n".join(lines)
