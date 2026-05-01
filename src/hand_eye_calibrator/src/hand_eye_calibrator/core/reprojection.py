from __future__ import annotations

import numpy as np
import cv2


def reprojection_error_px(
    points_3d, corners_2d, rvec, tvec, camera_matrix, dist_coeffs
) -> float:
    """计算投影点与观测点之间的平均重投影误差

    Args:
        points_3d (Any): 参数 points_3d
        corners_2d (Any): 参数 corners_2d
        rvec (Any): 参数 rvec
        tvec (Any): 参数 tvec
        camera_matrix (Any): 参数 camera_matrix
        dist_coeffs (Any): 参数 dist_coeffs

    Returns:
        float: 函数执行结果
    """
    projected, _ = cv2.projectPoints(points_3d, rvec, tvec, camera_matrix, dist_coeffs)
    projected = projected.reshape(-1, 2)
    observed = np.asarray(corners_2d, dtype=np.float64).reshape(-1, 2)
    return float(np.sqrt(np.mean(np.sum((projected - observed) ** 2, axis=1))))
