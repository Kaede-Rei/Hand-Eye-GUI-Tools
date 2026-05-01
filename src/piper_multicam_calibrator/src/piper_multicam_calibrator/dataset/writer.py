from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import cv2

from piper_multicam_calibrator.boards.base import BoardObservation
from piper_multicam_calibrator.core.io import ensure_dir, write_data
from piper_multicam_calibrator.core.transform import transform_to_dict


def next_sample_id(dataset_root: Path) -> int:
    samples_root = dataset_root / "samples"
    if not samples_root.exists():
        return 1
    ids = [int(p.name) for p in samples_root.iterdir() if p.is_dir() and p.name.isdigit()]
    return max(ids, default=0) + 1


def write_sample(
    dataset_root: Path,
    sample_id: int,
    camera_payloads: Dict[str, dict],
    T_base_tool=None,
    used_for=None,
    sync_payload: Optional[dict] = None,
) -> Path:
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
            "valid": {name: bool(payload.get("observation") and payload["observation"].ok) for name, payload in camera_payloads.items()},
        },
    )
    if T_base_tool is not None:
        write_data(
            sample_dir / "robot_pose.yaml",
            {
                "base_frame": "base_link",
                "tool_frame": "link_tcp",
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
