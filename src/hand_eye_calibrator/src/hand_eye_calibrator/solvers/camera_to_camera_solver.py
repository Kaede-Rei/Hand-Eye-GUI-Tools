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


class CameraToCameraSolver:
    def solve(
        self, task: CalibrationTask, records: Sequence[SampleRecord]
    ) -> CalibrationResult:
        if not task.reference_camera or not task.target_camera:
            raise ValueError(
                "camera_to_camera task requires reference_camera and target_camera"
            )
        valid = [
            r
            for r in records
            if task.reference_camera in r.cameras
            and task.target_camera in r.cameras
            and r.cameras[task.reference_camera].ok
            and r.cameras[task.target_camera].ok
            and r.cameras[task.reference_camera].T_camera_board is not None
            and r.cameras[task.target_camera].T_camera_board is not None
        ]
        if len(valid) < 3:
            raise ValueError(
                f"camera_to_camera requires at least 3 valid samples, got {len(valid)}"
            )
        estimates = [
            r.cameras[task.reference_camera].T_camera_board
            @ invert_transform(r.cameras[task.target_camera].T_camera_board)
            for r in valid
        ]
        T_ref_target = average_transforms(estimates)
        metrics = transform_residual_metrics(T_ref_target, estimates)
        metrics.update(
            scalar_error_stats(
                [
                    r.cameras[task.reference_camera].reprojection_error_px
                    for r in valid
                ],
                "reference_reprojection_error_px",
            )
        )
        metrics.update(
            scalar_error_stats(
                [r.cameras[task.target_camera].reprojection_error_px for r in valid],
                "target_reprojection_error_px",
            )
        )
        per_sample = []
        ref_inv = invert_transform(T_ref_target)
        for record, estimate in zip(valid, estimates):
            E = ref_inv @ estimate
            per_sample.append(
                {
                    "sample_id": record.sample_id,
                    "translation_error_m": float(np.linalg.norm(E[:3, 3])),
                    "reference_reprojection_error_px": record.cameras[
                        task.reference_camera
                    ].reprojection_error_px,
                    "target_reprojection_error_px": record.cameras[
                        task.target_camera
                    ].reprojection_error_px,
                }
            )
        return CalibrationResult(
            task.name,
            task.type,
            task.output_parent,
            task.output_child,
            T_ref_target,
            [r.sample_id for r in valid],
            metrics,
            per_sample,
        )
