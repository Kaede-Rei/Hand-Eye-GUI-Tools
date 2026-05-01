from __future__ import annotations

from typing import Sequence

import numpy as np

from hand_eye_calibrator.core.transform import (
    average_transforms,
    invert_transform,
    scalar_error_stats,
    transform_residual_metrics,
)
from hand_eye_calibrator.dataset.schema import CalibrationTask, SampleRecord
from hand_eye_calibrator.solvers.base import CalibrationResult


class EyeToHandKnownBoardSolver:
    def __init__(self, T_tool_board=None, iterations: int = 25):
        self.T_tool_board = T_tool_board
        self.iterations = int(iterations)

    def solve(
        self, task: CalibrationTask, records: Sequence[SampleRecord]
    ) -> CalibrationResult:
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
        if self.T_tool_board is None:
            return self._solve_unknown_board(task, valid)
        estimates = [
            r.T_base_tool
            @ self.T_tool_board
            @ invert_transform(r.cameras[task.camera].T_camera_board)
            for r in valid
        ]
        T_base_camera = average_transforms(estimates)
        metrics = transform_residual_metrics(T_base_camera, estimates)
        metrics.update(
            scalar_error_stats(
                [r.cameras[task.camera].reprojection_error_px for r in valid],
                "reprojection_error_px",
            )
        )
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

    def _solve_unknown_board(self, task: CalibrationTask, valid) -> CalibrationResult:
        T_tool_board = np.eye(4, dtype=np.float64)
        T_base_camera = np.eye(4, dtype=np.float64)
        for _ in range(max(1, self.iterations)):
            camera_estimates = [
                r.T_base_tool
                @ T_tool_board
                @ invert_transform(r.cameras[task.camera].T_camera_board)
                for r in valid
            ]
            T_base_camera = average_transforms(camera_estimates)
            board_estimates = [
                invert_transform(r.T_base_tool)
                @ T_base_camera
                @ r.cameras[task.camera].T_camera_board
                for r in valid
            ]
            T_tool_board = average_transforms(board_estimates)

        estimates = [
            r.T_base_tool
            @ T_tool_board
            @ invert_transform(r.cameras[task.camera].T_camera_board)
            for r in valid
        ]
        metrics = transform_residual_metrics(T_base_camera, estimates)
        board_metrics = transform_residual_metrics(
            T_tool_board,
            [
                invert_transform(r.T_base_tool)
                @ T_base_camera
                @ r.cameras[task.camera].T_camera_board
                for r in valid
            ],
        )
        metrics.update({f"tool_board_{k}": v for k, v in board_metrics.items()})
        metrics.update(
            scalar_error_stats(
                [r.cameras[task.camera].reprojection_error_px for r in valid],
                "reprojection_error_px",
            )
        )
        metrics["mode"] = "unknown_T_tool_board_alternating_average"
        metrics["iterations"] = self.iterations
        from hand_eye_calibrator.core.transform import transform_to_dict

        metrics["estimated_T_tool_board"] = transform_to_dict(T_tool_board)

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
