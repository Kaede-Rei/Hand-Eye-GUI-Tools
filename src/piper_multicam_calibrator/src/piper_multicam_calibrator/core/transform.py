from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

import numpy as np


def make_transform(rotation: np.ndarray, translation_xyz: Sequence[float]) -> np.ndarray:
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = np.asarray(rotation, dtype=np.float64).reshape(3, 3)
    T[:3, 3] = np.asarray(translation_xyz, dtype=np.float64).reshape(3)
    return T


def invert_transform(T: np.ndarray) -> np.ndarray:
    T = np.asarray(T, dtype=np.float64).reshape(4, 4)
    inv = np.eye(4, dtype=np.float64)
    inv[:3, :3] = T[:3, :3].T
    inv[:3, 3] = -inv[:3, :3] @ T[:3, 3]
    return inv


def rotation_angle_deg(R: np.ndarray) -> float:
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)
    value = (np.trace(R) - 1.0) / 2.0
    value = float(np.clip(value, -1.0, 1.0))
    return math.degrees(math.acos(value))


def matrix_to_quaternion_xyzw(R: np.ndarray) -> Tuple[float, float, float, float]:
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)
    trace = float(np.trace(R))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        qw = 0.25 * s
        qx = (R[2, 1] - R[1, 2]) / s
        qy = (R[0, 2] - R[2, 0]) / s
        qz = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    q = np.array([qx, qy, qz, qw], dtype=np.float64)
    q /= np.linalg.norm(q)
    return tuple(float(v) for v in q)


def quaternion_xyzw_to_matrix(q: Sequence[float]) -> np.ndarray:
    qx, qy, qz, qw = [float(v) for v in q]
    n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
    if n <= 0.0:
        return np.eye(3, dtype=np.float64)
    qx, qy, qz, qw = qx / n, qy / n, qz / n, qw / n
    return np.array(
        [
            [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
            [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
            [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)],
        ],
        dtype=np.float64,
    )


def transform_to_dict(T: np.ndarray) -> dict:
    T = np.asarray(T, dtype=np.float64).reshape(4, 4)
    return {
        "translation": [float(v) for v in T[:3, 3]],
        "rotation_xyzw": list(matrix_to_quaternion_xyzw(T[:3, :3])),
        "matrix": T.tolist(),
    }


def transform_from_dict(payload: dict) -> np.ndarray:
    if payload is None:
        raise ValueError("empty transform payload")
    if "matrix" in payload and payload["matrix"] is not None:
        return np.asarray(payload["matrix"], dtype=np.float64).reshape(4, 4)
    if "translation" in payload and "rotation_xyzw" in payload:
        return make_transform(
            quaternion_xyzw_to_matrix(payload["rotation_xyzw"]),
            payload["translation"],
        )
    raise ValueError("transform payload must contain matrix or translation+rotation_xyzw")


def quaternion_average_xyzw(quaternions: Iterable[Sequence[float]]) -> np.ndarray:
    A = np.zeros((4, 4), dtype=np.float64)
    ref = None
    count = 0
    for q_raw in quaternions:
        q = np.asarray(q_raw, dtype=np.float64).reshape(4)
        q /= np.linalg.norm(q)
        if ref is None:
            ref = q
        elif float(np.dot(ref, q)) < 0.0:
            q = -q
        A += np.outer(q, q)
        count += 1
    if count == 0:
        raise ValueError("cannot average zero quaternions")
    eigvals, eigvecs = np.linalg.eigh(A / count)
    q = eigvecs[:, int(np.argmax(eigvals))]
    if q[3] < 0.0:
        q = -q
    return q / np.linalg.norm(q)


def average_transforms(transforms: Sequence[np.ndarray]) -> np.ndarray:
    if not transforms:
        raise ValueError("cannot average zero transforms")
    translations = np.array([np.asarray(T)[:3, 3] for T in transforms], dtype=np.float64)
    quaternions = [matrix_to_quaternion_xyzw(np.asarray(T)[:3, :3]) for T in transforms]
    q = quaternion_average_xyzw(quaternions)
    return make_transform(quaternion_xyzw_to_matrix(q), np.median(translations, axis=0))


def transform_residual_metrics(reference: np.ndarray, estimates: Sequence[np.ndarray]) -> dict:
    if not estimates:
        return {"translation_rms_m": None, "translation_max_m": None, "rotation_rms_deg": None, "rotation_max_deg": None}
    t_errors = []
    r_errors = []
    ref_inv = invert_transform(reference)
    for T in estimates:
        E = ref_inv @ T
        t_errors.append(float(np.linalg.norm(E[:3, 3])))
        r_errors.append(rotation_angle_deg(E[:3, :3]))
    return {
        "translation_rms_m": float(np.sqrt(np.mean(np.square(t_errors)))),
        "translation_max_m": float(np.max(t_errors)),
        "rotation_rms_deg": float(np.sqrt(np.mean(np.square(r_errors)))),
        "rotation_max_deg": float(np.max(r_errors)),
    }
