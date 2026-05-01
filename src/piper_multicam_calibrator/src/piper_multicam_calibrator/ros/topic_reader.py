from __future__ import annotations

from typing import Dict

from piper_multicam_calibrator.ros.camera_cache import CameraCache


class RosTopicReader:
    def __init__(self):
        try:
            import rospy
            from sensor_msgs.msg import Image, CameraInfo
            from cv_bridge import CvBridge
        except Exception as exc:
            raise RuntimeError(f"ROS image dependencies are unavailable: {exc}")
        self.rospy = rospy
        self.Image = Image
        self.CameraInfo = CameraInfo
        self.bridge = CvBridge()
        self.cameras: Dict[str, CameraCache] = {}
        if not rospy.core.is_initialized():
            rospy.init_node("piper_multicam_calibrator_gui", anonymous=True, disable_signals=True)

    def connect_camera(self, name: str, image_topic: str, camera_info_topic: str, frame_id: str) -> CameraCache:
        cache = CameraCache(name, image_topic, camera_info_topic, frame_id)
        cache.image_sub = self.rospy.Subscriber(image_topic, self.Image, lambda msg, n=name: self._on_image(n, msg), queue_size=1)
        cache.info_sub = self.rospy.Subscriber(camera_info_topic, self.CameraInfo, lambda msg, n=name: self._on_info(n, msg), queue_size=1)
        self.cameras[name] = cache
        return cache

    def _stamp_sec(self, msg) -> float:
        try:
            return float(msg.header.stamp.to_sec())
        except Exception:
            return self.rospy.Time.now().to_sec()

    def _on_image(self, name: str, msg) -> None:
        cache = self.cameras.get(name)
        if cache is None:
            return
        cache.last_image_msg = msg
        cache.last_stamp_sec = self._stamp_sec(msg)
        cache.last_cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def _on_info(self, name: str, msg) -> None:
        cache = self.cameras.get(name)
        if cache is None:
            return
        cache.last_camera_info = {
            "width": int(msg.width),
            "height": int(msg.height),
            "frame_id": msg.header.frame_id,
            "distortion_model": msg.distortion_model,
            "K": list(msg.K),
            "D": list(msg.D),
            "R": list(msg.R),
            "P": list(msg.P),
            "stamp_sec": self._stamp_sec(msg),
        }

    def shutdown(self) -> None:
        for cache in self.cameras.values():
            if cache.image_sub is not None:
                cache.image_sub.unregister()
            if cache.info_sub is not None:
                cache.info_sub.unregister()
        self.cameras.clear()
