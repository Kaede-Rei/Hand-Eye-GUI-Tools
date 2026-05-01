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
    last_camera_info: Optional[dict] = None
    last_stamp_sec: Optional[float] = None
    image_sub: object = None
    info_sub: object = None
