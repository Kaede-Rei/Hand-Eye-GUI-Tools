from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class BoardObservation:
    ok: bool
    board_type: str
    message: str = ""
    corners_count: int = 0
    reprojection_error_px: Optional[float] = None
    image_size: Optional[tuple] = None
    corners_2d: Optional[np.ndarray] = None
    points_3d: Optional[np.ndarray] = None
    T_camera_board: Optional[np.ndarray] = None
    rvec: Optional[np.ndarray] = None
    tvec: Optional[np.ndarray] = None
    annotated_image: Optional[np.ndarray] = None

    def to_yaml_payload(self) -> dict:
        return {
            "board_type": self.board_type,
            "ok": bool(self.ok),
            "message": self.message,
            "corners_count": int(self.corners_count),
            "reprojection_error_px": self.reprojection_error_px,
            "image_size": list(self.image_size) if self.image_size else None,
            "T_camera_board": {"matrix": self.T_camera_board.tolist()} if self.T_camera_board is not None else None,
            "rvec": self.rvec.reshape(-1).tolist() if self.rvec is not None else None,
            "tvec_m": self.tvec.reshape(-1).tolist() if self.tvec is not None else None,
        }
