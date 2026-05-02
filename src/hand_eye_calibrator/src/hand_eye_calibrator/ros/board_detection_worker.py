from __future__ import annotations

import json
import sys

import numpy as np

from hand_eye_calibrator.boards import create_board_detector


def _array_payload(obs, name: str, payload: dict, arrays: dict) -> None:
    value = getattr(obs, name)
    if value is None:
        payload[name] = None
        return
    payload[name] = name
    arrays[name] = value


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: python -m hand_eye_calibrator.ros.board_detection_worker <input.npz> <output.npz>",
            file=sys.stderr,
        )
        return 2

    data = np.load(sys.argv[1], allow_pickle=False)
    config = json.loads(str(data["board_config"]))
    detector = create_board_detector(config)
    obs = detector.detect(data["image_bgr"], data["camera_matrix"], data["dist_coeffs"])

    payload = {
        "ok": bool(obs.ok),
        "board_type": obs.board_type,
        "message": obs.message,
        "corners_count": int(obs.corners_count),
        "reprojection_error_px": obs.reprojection_error_px,
        "image_size": list(obs.image_size) if obs.image_size else None,
    }
    arrays = {}
    for name in (
        "corners_2d",
        "points_3d",
        "T_camera_board",
        "rvec",
        "tvec",
        "annotated_image",
    ):
        _array_payload(obs, name, payload, arrays)

    np.savez_compressed(sys.argv[2], meta=json.dumps(payload), **arrays)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
