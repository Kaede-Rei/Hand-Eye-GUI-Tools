from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

import numpy as np


def make_transform(
    rotation: np.ndarray, translation_xyz: Sequence[float]
) -> np.ndarray:
    """根据旋转矩阵和平移向量构造 4x4 齐次变换矩阵

    Args:
        rotation (np.ndarray): 参数 rotation
        translation_xyz (Sequence[float]): 参数 translation_xyz

    Returns:
        np.ndarray: 函数执行结果
    """
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = np.asarray(rotation, dtype=np.float64).reshape(3, 3)
    T[:3, 3] = np.asarray(translation_xyz, dtype=np.float64).reshape(3)
    return T


def invert_transform(T: np.ndarray) -> np.ndarray:
    """计算 4x4 齐次变换矩阵的逆变换

    Args:
        T (np.ndarray): 参数 T

    Returns:
        np.ndarray: 函数执行结果
    """
    T = np.asarray(T, dtype=np.float64).reshape(4, 4)
    inv = np.eye(4, dtype=np.float64)
    inv[:3, :3] = T[:3, :3].T
    inv[:3, 3] = -inv[:3, :3] @ T[:3, 3]
    return inv


def rotation_angle_deg(R: np.ndarray) -> float:
    """计算旋转矩阵对应的旋转角度

    Args:
        R (np.ndarray): 参数 R

    Returns:
        float: 函数执行结果
    """
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)
    value = (np.trace(R) - 1.0) / 2.0
    value = float(np.clip(value, -1.0, 1.0))
    return math.degrees(math.acos(value))


def matrix_to_quaternion_xyzw(R: np.ndarray) -> Tuple[float, float, float, float]:
    """将旋转矩阵转换为 xyzw 顺序四元数

    Args:
        R (np.ndarray): 参数 R

    Returns:
        Tuple[float, float, float, float]: 函数执行结果
    """
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
    """将 xyzw 顺序四元数转换为旋转矩阵

    Args:
        q (Sequence[float]): 参数 q

    Returns:
        np.ndarray: 函数执行结果
    """
    qx, qy, qz, qw = [float(v) for v in q]
    n = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw)
    if n <= 0.0:
        return np.eye(3, dtype=np.float64)
    qx, qy, qz, qw = qx / n, qy / n, qz / n, qw / n
    return np.array(
        [
            [
                1 - 2 * (qy * qy + qz * qz),
                2 * (qx * qy - qz * qw),
                2 * (qx * qz + qy * qw),
            ],
            [
                2 * (qx * qy + qz * qw),
                1 - 2 * (qx * qx + qz * qz),
                2 * (qy * qz - qx * qw),
            ],
            [
                2 * (qx * qz - qy * qw),
                2 * (qy * qz + qx * qw),
                1 - 2 * (qx * qx + qy * qy),
            ],
        ],
        dtype=np.float64,
    )


def transform_to_dict(T: np.ndarray) -> dict:
    """将齐次变换矩阵转换为可写入 YAML 的字典

    Args:
        T (np.ndarray): 参数 T

    Returns:
        dict: 函数执行结果
    """
    T = np.asarray(T, dtype=np.float64).reshape(4, 4)
    return {
        "translation": [float(v) for v in T[:3, 3]],
        "rotation_xyzw": list(matrix_to_quaternion_xyzw(T[:3, :3])),
        "matrix": T.tolist(),
    }


def transform_from_dict(payload: dict) -> np.ndarray:
    """从字典载入齐次变换矩阵

    Args:
        payload (dict): 参数 payload

    Returns:
        np.ndarray: 函数执行结果
    """
    if payload is None:
        raise ValueError("empty transform payload")
    if "matrix" in payload and payload["matrix"] is not None:
        return np.asarray(payload["matrix"], dtype=np.float64).reshape(4, 4)
    if "translation" in payload and "rotation_xyzw" in payload:
        return make_transform(
            quaternion_xyzw_to_matrix(payload["rotation_xyzw"]),
            payload["translation"],
        )
    raise ValueError(
        "transform payload must contain matrix or translation+rotation_xyzw"
    )


def quaternion_average_xyzw(quaternions: Iterable[Sequence[float]]) -> np.ndarray:
    """对一组 xyzw 四元数进行符号一致的平均

    Args:
        quaternions (Iterable[Sequence[float]]): 参数 quaternions

    Returns:
        np.ndarray: 函数执行结果
    """
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
    """对一组齐次变换进行平移中位数和旋转平均融合

    Args:
        transforms (Sequence[np.ndarray]): 参数 transforms

    Returns:
        np.ndarray: 函数执行结果
    """
    if not transforms:
        raise ValueError("cannot average zero transforms")
    translations = np.array(
        [np.asarray(T)[:3, 3] for T in transforms], dtype=np.float64
    )
    quaternions = [matrix_to_quaternion_xyzw(np.asarray(T)[:3, :3]) for T in transforms]
    q = quaternion_average_xyzw(quaternions)
    return make_transform(quaternion_xyzw_to_matrix(q), np.median(translations, axis=0))


def transform_residual_metrics(
    reference: np.ndarray, estimates: Sequence[np.ndarray]
) -> dict:
    """计算一组变换相对参考变换的平移和旋转误差统计

    Args:
        reference (np.ndarray): 参数 reference
        estimates (Sequence[np.ndarray]): 参数 estimates

    Returns:
        dict: 函数执行结果
    """
    if not estimates:
        return {
            "translation_rms_m": None,
            "translation_mean_m": None,
            "translation_median_m": None,
            "translation_std_m": None,
            "translation_max_m": None,
            "rotation_rms_deg": None,
            "rotation_mean_deg": None,
            "rotation_median_deg": None,
            "rotation_std_deg": None,
            "rotation_max_deg": None,
        }
    t_errors = []
    r_errors = []
    ref_inv = invert_transform(reference)
    for T in estimates:
        E = ref_inv @ T
        t_errors.append(float(np.linalg.norm(E[:3, 3])))
        r_errors.append(rotation_angle_deg(E[:3, :3]))
    return {
        "translation_rms_m": float(np.sqrt(np.mean(np.square(t_errors)))),
        "translation_mean_m": float(np.mean(t_errors)),
        "translation_median_m": float(np.median(t_errors)),
        "translation_std_m": float(np.std(t_errors)),
        "translation_max_m": float(np.max(t_errors)),
        "rotation_rms_deg": float(np.sqrt(np.mean(np.square(r_errors)))),
        "rotation_mean_deg": float(np.mean(r_errors)),
        "rotation_median_deg": float(np.median(r_errors)),
        "rotation_std_deg": float(np.std(r_errors)),
        "rotation_max_deg": float(np.max(r_errors)),
    }


def scalar_error_stats(values: Sequence[float], prefix: str) -> dict:
    """计算一组标量误差的均值、中位数、标准差、RMS 和最大值

    Args:
        values (Sequence[float]): 参数 values
        prefix (str): 参数 prefix

    Returns:
        dict: 函数执行结果
    """
    clean = np.array([float(v) for v in values if v is not None], dtype=np.float64)
    if clean.size == 0:
        return {
            f"{prefix}_mean": None,
            f"{prefix}_median": None,
            f"{prefix}_std": None,
            f"{prefix}_rms": None,
            f"{prefix}_max": None,
        }
    return {
        f"{prefix}_mean": float(np.mean(clean)),
        f"{prefix}_median": float(np.median(clean)),
        f"{prefix}_std": float(np.std(clean)),
        f"{prefix}_rms": float(np.sqrt(np.mean(np.square(clean)))),
        f"{prefix}_max": float(np.max(clean)),
    }
