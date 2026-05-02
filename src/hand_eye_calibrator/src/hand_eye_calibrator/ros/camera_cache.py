from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class CameraCache:
    name: str
    image_topic: str
    camera_info_topic: str
    frame_id: str
    last_image_msg: object = None
    last_cv_image: object = None
    needs_preview: bool = False
    last_preview_convert_sec: Optional[float] = None
    last_camera_info: Optional[dict] = None
    last_stamp_sec: Optional[float] = None
    last_receive_sec: Optional[float] = None
    last_input_latency_ms: Optional[float] = None
    last_convert_ms: Optional[float] = None
    input_fps: Optional[float] = None
    input_fps_started: Optional[float] = None
    input_fps_frames: int = 0
    image_sub: object = None
    info_sub: object = None
