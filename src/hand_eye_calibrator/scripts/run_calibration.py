#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hand_eye_calibrator.core.io import read_data
from hand_eye_calibrator.core.transform import transform_from_dict
from hand_eye_calibrator.dataset.loader import load_dataset_records
from hand_eye_calibrator.dataset.schema import CalibrationTask
from hand_eye_calibrator.report.exporter import export_result
from hand_eye_calibrator.solvers import create_solver


def _task_from_payload(payload: dict) -> CalibrationTask:
    """从配置字典构造标定任务对象

    Args:
        payload (dict): 参数 payload

    Returns:
        CalibrationTask: 函数执行结果
    """
    return CalibrationTask(
        name=payload["name"],
        type=payload["type"],
        camera=payload.get("camera"),
        reference_camera=payload.get("reference_camera"),
        target_camera=payload.get("target_camera"),
        output_parent=payload["output_parent"],
        output_child=payload["output_child"],
    )


def main() -> None:
    """命令行入口，解析参数并执行对应流程

    Args:
        None: 无输入参数

    Returns:
        None: 无返回值
    """
    parser = argparse.ArgumentParser(
        description="Run one multi-function hand-eye calibration task."
    )
    parser.add_argument("--config", default=str(ROOT / "config" / "default.yaml"))
    parser.add_argument("--task", required=True)
    parser.add_argument("--min-id", type=int)
    parser.add_argument("--max-id", type=int)
    parser.add_argument(
        "--t-tool-board-yaml",
        help="YAML containing T_tool_board for eye_to_hand_known_board",
    )
    args = parser.parse_args()

    cfg = read_data(Path(args.config))
    task_payload = next(t for t in cfg["calibration_tasks"] if t["name"] == args.task)
    task = _task_from_payload(task_payload)
    cameras = list(cfg["cameras"].keys())
    dataset_root = Path(cfg["project"]["dataset_root"])
    output_root = Path(cfg["project"]["output_root"])
    records = load_dataset_records(dataset_root, cameras, args.min_id, args.max_id)
    kwargs = {}
    if task.type in ("eye_to_hand", "eye_to_hand_known_board"):
        if args.t_tool_board_yaml:
            kwargs["T_tool_board"] = transform_from_dict(
                read_data(Path(args.t_tool_board_yaml))["T_tool_board"]
            )
    result = create_solver(task.type, **kwargs).solve(task, records)
    out = export_result(output_root, result)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
