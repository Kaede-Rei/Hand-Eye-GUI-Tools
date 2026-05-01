from __future__ import annotations

import numpy as np
import cv2

from piper_multicam_calibrator.boards.base import BoardObservation
from piper_multicam_calibrator.core.reprojection import reprojection_error_px
from piper_multicam_calibrator.core.transform import make_transform


class ChessboardDetector:
    def __init__(self, config: dict):
        self.config = dict(config)
        self.cols = int(config.get("cols", config.get("columns", 9)))
        self.rows = int(config.get("rows", 6))
        self.square_size_m = float(config.get("square_size_m", 0.025))

    def object_points(self) -> np.ndarray:
        obj = np.zeros((self.cols * self.rows, 3), dtype=np.float64)
        obj[:, :2] = np.mgrid[0 : self.cols, 0 : self.rows].T.reshape(-1, 2)
        obj *= self.square_size_m
        return obj

    def detect(self, image_bgr, camera_matrix, dist_coeffs) -> BoardObservation:
        if image_bgr is None:
            return BoardObservation(False, "chessboard", "empty image")
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        pattern = (self.cols, self.rows)
        found = False
        corners = None
        if hasattr(cv2, "findChessboardCornersSB"):
            found, corners = cv2.findChessboardCornersSB(gray, pattern)
        if not found:
            flags = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE
            found, corners = cv2.findChessboardCorners(gray, pattern, flags)
            if found:
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.001)
                corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        annotated = image_bgr.copy()
        if not found:
            return BoardObservation(
                False,
                "chessboard",
                "chessboard corners not found",
                image_size=(image_bgr.shape[1], image_bgr.shape[0]),
                annotated_image=annotated,
            )
        points_3d = self.object_points()
        ok, rvec, tvec = cv2.solvePnP(points_3d, corners, camera_matrix, dist_coeffs)
        if ok and hasattr(cv2, "solvePnPRefineLM"):
            rvec, tvec = cv2.solvePnPRefineLM(points_3d, corners, camera_matrix, dist_coeffs, rvec, tvec)
        if not ok:
            return BoardObservation(False, "chessboard", "solvePnP failed", corners_count=len(corners), annotated_image=annotated)
        err = reprojection_error_px(points_3d, corners, rvec, tvec, camera_matrix, dist_coeffs)
        R, _ = cv2.Rodrigues(rvec)
        T = make_transform(R, tvec.reshape(3))
        cv2.drawChessboardCorners(annotated, pattern, corners, True)
        try:
            cv2.drawFrameAxes(annotated, camera_matrix, dist_coeffs, rvec, tvec, self.square_size_m * 2.0, 2)
        except Exception:
            pass
        return BoardObservation(
            True,
            "chessboard",
            "ok",
            corners_count=len(corners),
            reprojection_error_px=err,
            image_size=(image_bgr.shape[1], image_bgr.shape[0]),
            corners_2d=corners.reshape(-1, 2),
            points_3d=points_3d,
            T_camera_board=T,
            rvec=rvec.reshape(3, 1),
            tvec=tvec.reshape(3, 1),
            annotated_image=annotated,
        )
