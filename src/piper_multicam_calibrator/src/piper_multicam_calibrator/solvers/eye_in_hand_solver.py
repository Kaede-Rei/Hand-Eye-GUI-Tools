from __future__ import annotations

from typing import Sequence

import cv2
import numpy as np

from piper_multicam_calibrator.core.transform import invert_transform, make_transform, transform_residual_metrics
from piper_multicam_calibrator.dataset.schema import CalibrationTask, SampleRecord
from piper_multicam_calibrator.solvers.base import CalibrationResult


_METHODS = {
    "TSAI": cv2.CALIB_HAND_EYE_TSAI,
    "PARK": cv2.CALIB_HAND_EYE_PARK,
    "HORAUD": cv2.CALIB_HAND_EYE_HORAUD,
    "ANDREFF": cv2.CALIB_HAND_EYE_ANDREFF,
    "DANIILIDIS": cv2.CALIB_HAND_EYE_DANIILIDIS,
}


class EyeInHandSolver:
    def __init__(self, method: str = "TSAI"):
        self.method = method.upper()

    def solve(self, task: CalibrationTask, records: Sequence[SampleRecord]) -> CalibrationResult:
        if not task.camera:
            raise ValueError("eye_in_hand task requires camera")
        valid = [
            r for r in records
            if r.T_base_tool is not None
            and task.camera in r.cameras
            and r.cameras[task.camera].ok
            and r.cameras[task.camera].T_camera_board is not None
        ]
        if len(valid) < 3:
            raise ValueError(f"eye_in_hand requires at least 3 valid samples, got {len(valid)}")
        R_gripper2base = [r.T_base_tool[:3, :3] for r in valid]
        t_gripper2base = [r.T_base_tool[:3, 3].reshape(3, 1) for r in valid]
        R_target2cam = [r.cameras[task.camera].T_camera_board[:3, :3] for r in valid]
        t_target2cam = [r.cameras[task.camera].T_camera_board[:3, 3].reshape(3, 1) for r in valid]
        R_cam2gripper, t_cam2gripper = cv2.calibrateHandEye(
            R_gripper2base,
            t_gripper2base,
            R_target2cam,
            t_target2cam,
            method=_METHODS.get(self.method, cv2.CALIB_HAND_EYE_TSAI),
        )
        T_tool_camera = make_transform(R_cam2gripper, t_cam2gripper.reshape(3))
        board_in_base = [r.T_base_tool @ T_tool_camera @ r.cameras[task.camera].T_camera_board for r in valid]
        mean_board = board_in_base[0]
        metrics = transform_residual_metrics(mean_board, board_in_base)
        per_sample = []
        for record, T_base_board in zip(valid, board_in_base):
            E = invert_transform(mean_board) @ T_base_board
            per_sample.append(
                {
                    "sample_id": record.sample_id,
                    "board_translation_error_m": float(np.linalg.norm(E[:3, 3])),
                    "reprojection_error_px": record.cameras[task.camera].reprojection_error_px,
                }
            )
        metrics["method"] = self.method
        return CalibrationResult(
            task.name,
            task.type,
            task.output_parent,
            task.output_child,
            T_tool_camera,
            [r.sample_id for r in valid],
            metrics,
            per_sample,
        )
