from __future__ import annotations

import numpy as np
import cv2

from hand_eye_calibrator.boards.base import BoardObservation
from hand_eye_calibrator.core.reprojection import reprojection_error_px
from hand_eye_calibrator.core.transform import make_transform

_DICT_NAMES = (
    {
        name: getattr(cv2.aruco, name)
        for name in dir(cv2.aruco)
        if name.startswith("DICT_")
    }
    if hasattr(cv2, "aruco")
    else {}
)


class CharucoDetector:
    def __init__(self, config: dict):
        if not hasattr(cv2, "aruco"):
            raise RuntimeError(
                "OpenCV aruco module is unavailable; install opencv-contrib-python or ROS cv2 with aruco"
            )
        self.config = dict(config)
        self.squares_x = int(config.get("squares_x", 8))
        self.squares_y = int(config.get("squares_y", 11))
        self.square_length_m = float(config.get("square_length_m", 0.030))
        self.marker_length_m = float(config.get("marker_length_m", 0.022))
        dict_name = str(config.get("dictionary", "DICT_5X5_100"))
        dictionary_id = _DICT_NAMES.get(dict_name)
        if dictionary_id is None:
            raise ValueError(f"unsupported ChArUco dictionary: {dict_name}")
        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.board = cv2.aruco.CharucoBoard_create(
            self.squares_x,
            self.squares_y,
            self.square_length_m,
            self.marker_length_m,
            self.dictionary,
        )

    def detect(self, image_bgr, camera_matrix, dist_coeffs) -> BoardObservation:
        if image_bgr is None:
            return BoardObservation(False, "charuco", "empty image")
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        annotated = image_bgr.copy()
        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.dictionary)
        if ids is None or len(ids) == 0:
            return BoardObservation(
                False,
                "charuco",
                "aruco markers not found",
                image_size=(image_bgr.shape[1], image_bgr.shape[0]),
                annotated_image=annotated,
            )
        cv2.aruco.drawDetectedMarkers(annotated, corners, ids)
        ok_count, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
            corners, ids, gray, self.board, camera_matrix, dist_coeffs
        )
        if charuco_ids is None or ok_count < 4:
            return BoardObservation(
                False,
                "charuco",
                "not enough ChArUco corners",
                corners_count=int(ok_count or 0),
                annotated_image=annotated,
            )
        ok, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(
            charuco_corners,
            charuco_ids,
            self.board,
            camera_matrix,
            dist_coeffs,
            None,
            None,
        )
        if not ok:
            return BoardObservation(
                False,
                "charuco",
                "estimatePoseCharucoBoard failed",
                corners_count=int(ok_count),
                annotated_image=annotated,
            )
        obj_points = []
        img_points = []
        chessboard_corners = np.asarray(self.board.chessboardCorners, dtype=np.float64)
        for idx, corner in zip(charuco_ids.reshape(-1), charuco_corners.reshape(-1, 2)):
            obj_points.append(chessboard_corners[int(idx)])
            img_points.append(corner)
        obj_points = np.asarray(obj_points, dtype=np.float64).reshape(-1, 3)
        img_points = np.asarray(img_points, dtype=np.float64).reshape(-1, 2)
        if hasattr(cv2, "solvePnPRefineLM"):
            rvec, tvec = cv2.solvePnPRefineLM(
                obj_points, img_points, camera_matrix, dist_coeffs, rvec, tvec
            )
        err = reprojection_error_px(
            obj_points, img_points, rvec, tvec, camera_matrix, dist_coeffs
        )
        R, _ = cv2.Rodrigues(rvec)
        T = make_transform(R, tvec.reshape(3))
        cv2.aruco.drawDetectedCornersCharuco(annotated, charuco_corners, charuco_ids)
        try:
            cv2.drawFrameAxes(
                annotated,
                camera_matrix,
                dist_coeffs,
                rvec,
                tvec,
                self.square_length_m * 2.0,
                2,
            )
        except Exception:
            pass
        return BoardObservation(
            True,
            "charuco",
            "ok",
            corners_count=int(ok_count),
            reprojection_error_px=err,
            image_size=(image_bgr.shape[1], image_bgr.shape[0]),
            corners_2d=img_points,
            points_3d=obj_points,
            T_camera_board=T,
            rvec=rvec.reshape(3, 1),
            tvec=tvec.reshape(3, 1),
            annotated_image=annotated,
        )
