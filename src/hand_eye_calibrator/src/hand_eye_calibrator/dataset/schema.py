from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import numpy as np


@dataclass
class CameraConfig:
    name: str
    image_topic: str
    camera_info_topic: str
    frame_id: str
    role: str = ""


@dataclass
class RobotConfig:
    base_frame: str = "base_link"
    tool_frame: str = "link_tcp"
    tf_timeout_sec: float = 0.3


@dataclass
class CalibrationTask:
    name: str
    type: str
    output_parent: str
    output_child: str
    camera: Optional[str] = None
    reference_camera: Optional[str] = None
    target_camera: Optional[str] = None


@dataclass
class CameraObservationRecord:
    camera_name: str
    sample_dir: Path
    image_path: Path
    detection_path: Path
    camera_info_path: Optional[Path]
    T_camera_board: Optional[np.ndarray]
    reprojection_error_px: Optional[float]
    corners_count: int
    ok: bool


@dataclass
class SampleRecord:
    sample_id: int
    sample_dir: Path
    T_base_tool: Optional[np.ndarray]
    cameras: Dict[str, CameraObservationRecord]
