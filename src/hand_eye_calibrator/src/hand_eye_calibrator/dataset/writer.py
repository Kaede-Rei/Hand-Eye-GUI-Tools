from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import cv2

from hand_eye_calibrator.boards.base import BoardObservation
from hand_eye_calibrator.core.io import ensure_dir, write_data
from hand_eye_calibrator.core.transform import transform_to_dict


def next_sample_id(dataset_root: Path) -> int:
    """计算数据集中下一个可用样本编号

    Args:
        dataset_root (Path): 参数 dataset_root

    Returns:
        int: 函数执行结果
    """
    samples_root = dataset_root / "samples"
    if not samples_root.exists():
        return 1
    ids = [
        int(p.name) for p in samples_root.iterdir() if p.is_dir() and p.name.isdigit()
    ]
    return max(ids, default=0) + 1


def write_sample(
    dataset_root: Path,
    sample_id: int,
    camera_payloads: Dict[str, dict],
    T_base_tool=None,
    robot_parent_frame: str = "base_link",
    robot_child_frame: str = "link_tcp",
    used_for=None,
    sync_payload: Optional[dict] = None,
) -> Path:
    """将一次采样的图像、内参、检测结果和机器人位姿写入数据集

    Args:
        dataset_root (Path): 参数 dataset_root
        sample_id (int): 参数 sample_id
        camera_payloads (Dict[str, dict]): 参数 camera_payloads
        T_base_tool (Any): 参数 T_base_tool
        robot_parent_frame (str): 参数 robot_parent_frame
        robot_child_frame (str): 参数 robot_child_frame
        used_for (Any): 参数 used_for
        sync_payload (Optional[dict]): 参数 sync_payload

    Returns:
        Path: 函数执行结果
    """
    sample_dir = ensure_dir(dataset_root / "samples" / f"{sample_id:06d}")
    now = datetime.now().isoformat(timespec="milliseconds")
    write_data(
        sample_dir / "sample.yaml",
        {
            "sample_id": int(sample_id),
            "timestamp": now,
            "capture_mode": "manual_click",
            "used_for": list(used_for or []),
            "time_sync": sync_payload or {},
            "valid": {
                name: bool(payload.get("observation") and payload["observation"].ok)
                for name, payload in camera_payloads.items()
            },
        },
    )
    if T_base_tool is not None:
        write_data(
            sample_dir / "robot_pose.yaml",
            {
                "base_frame": robot_parent_frame,
                "tool_frame": robot_child_frame,
                "T_base_tool": transform_to_dict(T_base_tool),
                "source": "tf2",
                "timestamp": now,
            },
        )
    for camera_name, payload in camera_payloads.items():
        camera_dir = ensure_dir(sample_dir / camera_name)
        image = payload.get("image")
        if image is not None:
            cv2.imwrite(str(camera_dir / "image.png"), image)
        camera_info = payload.get("camera_info")
        if camera_info is not None:
            write_data(camera_dir / "camera_info.yaml", camera_info)
        obs: Optional[BoardObservation] = payload.get("observation")
        if obs is not None:
            write_data(camera_dir / "detection.yaml", obs.to_yaml_payload())
            if obs.annotated_image is not None:
                cv2.imwrite(str(camera_dir / "annotated.png"), obs.annotated_image)
    return sample_dir
