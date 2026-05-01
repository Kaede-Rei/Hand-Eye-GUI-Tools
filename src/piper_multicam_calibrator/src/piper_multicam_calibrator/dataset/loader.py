from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence

from piper_multicam_calibrator.core.io import read_data
from piper_multicam_calibrator.core.transform import transform_from_dict
from piper_multicam_calibrator.dataset.schema import CameraObservationRecord, SampleRecord


def list_sample_dirs(dataset_root: Path, min_id: Optional[int] = None, max_id: Optional[int] = None) -> List[Path]:
    samples_root = dataset_root / "samples"
    if not samples_root.exists():
        return []
    dirs = []
    for child in samples_root.iterdir():
        if not child.is_dir() or not child.name.isdigit():
            continue
        idx = int(child.name)
        if min_id is not None and idx < min_id:
            continue
        if max_id is not None and idx > max_id:
            continue
        dirs.append(child)
    return sorted(dirs, key=lambda p: int(p.name))


def _load_robot_pose(sample_dir: Path):
    path = sample_dir / "robot_pose.yaml"
    if not path.exists():
        return None
    payload = read_data(path)
    return transform_from_dict(payload.get("T_base_tool"))


def _load_camera_observation(sample_dir: Path, camera_name: str) -> Optional[CameraObservationRecord]:
    camera_dir = sample_dir / camera_name
    detection_path = camera_dir / "detection.yaml"
    image_path = camera_dir / "image.png"
    camera_info_path = camera_dir / "camera_info.yaml"
    if not detection_path.exists():
        return None
    payload = read_data(detection_path)
    T = None
    if payload.get("ok") and payload.get("T_camera_board"):
        T = transform_from_dict(payload["T_camera_board"])
    return CameraObservationRecord(
        camera_name=camera_name,
        sample_dir=sample_dir,
        image_path=image_path,
        detection_path=detection_path,
        camera_info_path=camera_info_path if camera_info_path.exists() else None,
        T_camera_board=T,
        reprojection_error_px=payload.get("reprojection_error_px"),
        corners_count=int(payload.get("corners_count") or 0),
        ok=bool(payload.get("ok")),
    )


def load_dataset_records(
    dataset_root: Path,
    camera_names: Sequence[str],
    min_id: Optional[int] = None,
    max_id: Optional[int] = None,
) -> List[SampleRecord]:
    records: List[SampleRecord] = []
    for sample_dir in list_sample_dirs(dataset_root, min_id, max_id):
        cameras: Dict[str, CameraObservationRecord] = {}
        for name in camera_names:
            obs = _load_camera_observation(sample_dir, name)
            if obs is not None:
                cameras[name] = obs
        records.append(
            SampleRecord(
                sample_id=int(sample_dir.name),
                sample_dir=sample_dir,
                T_base_tool=_load_robot_pose(sample_dir),
                cameras=cameras,
            )
        )
    return records
