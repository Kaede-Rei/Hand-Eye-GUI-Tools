from __future__ import annotations

import numpy as np
import cv2


def reprojection_error_px(points_3d, corners_2d, rvec, tvec, camera_matrix, dist_coeffs) -> float:
    projected, _ = cv2.projectPoints(points_3d, rvec, tvec, camera_matrix, dist_coeffs)
    projected = projected.reshape(-1, 2)
    observed = np.asarray(corners_2d, dtype=np.float64).reshape(-1, 2)
    return float(np.sqrt(np.mean(np.sum((projected - observed) ** 2, axis=1))))
