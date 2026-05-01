from __future__ import annotations

import numpy as np

from hand_eye_calibrator.core.transform import make_transform, quaternion_xyzw_to_matrix


class TfReader:
    def __init__(self):
        """初始化对象并保存运行所需的状态

        Args:
            None: 无输入参数

        Returns:
            None: 无返回值
        """
        try:
            import rospy
            import tf2_ros
        except Exception as exc:
            raise RuntimeError(f"ROS tf2 dependencies are unavailable: {exc}")
        self.rospy = rospy
        self.tf2_ros = tf2_ros
        if not rospy.core.is_initialized():
            rospy.init_node(
                "hand_eye_calibrator_gui", anonymous=True, disable_signals=True
            )
        self.buffer = tf2_ros.Buffer(cache_time=rospy.Duration(30.0))
        self.listener = tf2_ros.TransformListener(self.buffer)

    def lookup(
        self, parent_frame: str, child_frame: str, timeout_sec: float = 0.3
    ) -> np.ndarray:
        """查询指定父子坐标系之间的 TF 变换

        Args:
            parent_frame (str): 参数 parent_frame
            child_frame (str): 参数 child_frame
            timeout_sec (float): 参数 timeout_sec

        Returns:
            np.ndarray: 函数执行结果
        """
        msg = self.buffer.lookup_transform(
            parent_frame,
            child_frame,
            self.rospy.Time(0),
            self.rospy.Duration(float(timeout_sec)),
        )
        tr = msg.transform.translation
        rot = msg.transform.rotation
        return make_transform(
            quaternion_xyzw_to_matrix([rot.x, rot.y, rot.z, rot.w]),
            [tr.x, tr.y, tr.z],
        )
