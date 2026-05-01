from __future__ import annotations

import numpy as np

from piper_multicam_calibrator.core.transform import make_transform, quaternion_xyzw_to_matrix


class TfReader:
    def __init__(self):
        try:
            import rospy
            import tf2_ros
        except Exception as exc:
            raise RuntimeError(f"ROS tf2 dependencies are unavailable: {exc}")
        self.rospy = rospy
        self.tf2_ros = tf2_ros
        if not rospy.core.is_initialized():
            rospy.init_node("piper_multicam_calibrator_gui", anonymous=True, disable_signals=True)
        self.buffer = tf2_ros.Buffer(cache_time=rospy.Duration(30.0))
        self.listener = tf2_ros.TransformListener(self.buffer)

    def lookup(self, parent_frame: str, child_frame: str, timeout_sec: float = 0.3) -> np.ndarray:
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
