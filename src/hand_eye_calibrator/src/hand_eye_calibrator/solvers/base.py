from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class CalibrationResult:
    task_name: str
    task_type: str
    parent_frame: str
    child_frame: str
    T_parent_child: np.ndarray
    sample_ids: List[int]
    metrics: dict = field(default_factory=dict)
    per_sample: list = field(default_factory=list)
    output_dir: Optional[str] = None

    def to_payload(self) -> dict:
        """将标定结果转换为 YAML 可序列化字典

        Args:
            None: 无输入参数

        Returns:
            dict: 函数执行结果
        """
        from hand_eye_calibrator.core.transform import transform_to_dict

        return {
            "task_name": self.task_name,
            "task_type": self.task_type,
            "parent_frame": self.parent_frame,
            "child_frame": self.child_frame,
            "T_parent_child": transform_to_dict(self.T_parent_child),
            "sample_ids": self.sample_ids,
            "metrics": self.metrics,
            "per_sample": self.per_sample,
        }
