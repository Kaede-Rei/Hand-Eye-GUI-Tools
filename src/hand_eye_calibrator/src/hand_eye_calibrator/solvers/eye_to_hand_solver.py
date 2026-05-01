from __future__ import annotations

from typing import Sequence

import numpy as np

from hand_eye_calibrator.core.transform import (
    average_transforms,
    invert_transform,
    transform_residual_metrics,
)
from hand_eye_calibrator.dataset.schema import CalibrationTask, SampleRecord
from hand_eye_calibrator.solvers.base import CalibrationResult


class EyeToHandKnownBoardSolver:
    def __init__(self, T_tool_board=None):
        self.T_tool_board = T_tool_board

    def solve(
        self, task: CalibrationTask, records: Sequence[SampleRecord]
    ) -> CalibrationResult:
        if self.T_tool_board is None:
            raise ValueError("eye_to_hand_known_board requires measured T_tool_board")
        if not task.camera:
            raise ValueError("eye_to_hand task requires camera")
        valid = [
            r
            for r in records
            if r.T_base_tool is not None
            and task.camera in r.cameras
            and r.cameras[task.camera].ok
            and r.cameras[task.camera].T_camera_board is not None
        ]
        if len(valid) < 3:
            raise ValueError(
                f"eye_to_hand_known_board requires at least 3 valid samples, got {len(valid)}"
            )
        estimates = [
            r.T_base_tool
            @ self.T_tool_board
            @ invert_transform(r.cameras[task.camera].T_camera_board)
            for r in valid
        ]
        T_base_camera = average_transforms(estimates)
        metrics = transform_residual_metrics(T_base_camera, estimates)
        per_sample = []
        ref_inv = invert_transform(T_base_camera)
        for record, estimate in zip(valid, estimates):
            E = ref_inv @ estimate
            per_sample.append(
                {
                    "sample_id": record.sample_id,
                    "translation_error_m": float(np.linalg.norm(E[:3, 3])),
                    "reprojection_error_px": record.cameras[
                        task.camera
                    ].reprojection_error_px,
                }
            )
        metrics["mode"] = "known_T_tool_board_direct_average"
        return CalibrationResult(
            task.name,
            task.type,
            task.output_parent,
            task.output_child,
            T_base_camera,
            [r.sample_id for r in valid],
            metrics,
            per_sample,
        )
