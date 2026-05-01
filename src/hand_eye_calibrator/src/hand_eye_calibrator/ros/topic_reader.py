from __future__ import annotations

from typing import Dict

from hand_eye_calibrator.ros.camera_cache import CameraCache


class RosTopicReader:
    def __init__(self):
        """初始化对象并保存运行所需的状态

        Args:
            None: 无输入参数

        Returns:
            None: 无返回值
        """
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
            rospy.init_node(
                "hand_eye_calibrator_gui", anonymous=True, disable_signals=True
            )

    def connect_camera(
        self, name: str, image_topic: str, camera_info_topic: str, frame_id: str
    ) -> CameraCache:
        """订阅单个相机的图像和 camera_info 话题

        Args:
            name (str): 参数 name
            image_topic (str): 参数 image_topic
            camera_info_topic (str): 参数 camera_info_topic
            frame_id (str): 参数 frame_id

        Returns:
            CameraCache: 函数执行结果
        """
        cache = CameraCache(name, image_topic, camera_info_topic, frame_id)
        cache.image_sub = self.rospy.Subscriber(
            image_topic,
            self.Image,
            lambda msg, n=name: self._on_image(n, msg),
            queue_size=1,
        )
        cache.info_sub = self.rospy.Subscriber(
            camera_info_topic,
            self.CameraInfo,
            lambda msg, n=name: self._on_info(n, msg),
            queue_size=1,
        )
        self.cameras[name] = cache
        return cache

    def _stamp_sec(self, msg) -> float:
        """将 ROS 消息时间戳转换为秒

        Args:
            msg (Any): 参数 msg

        Returns:
            float: 函数执行结果
        """
        try:
            return float(msg.header.stamp.to_sec())
        except Exception:
            return self.rospy.Time.now().to_sec()

    def _on_image(self, name: str, msg) -> None:
        """处理图像消息并更新相机缓存

        Args:
            name (str): 参数 name
            msg (Any): 参数 msg

        Returns:
            None: 无返回值
        """
        cache = self.cameras.get(name)
        if cache is None:
            return
        cache.last_image_msg = msg
        cache.last_stamp_sec = self._stamp_sec(msg)
        cache.last_cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def _on_info(self, name: str, msg) -> None:
        """处理 camera_info 消息并更新相机缓存

        Args:
            name (str): 参数 name
            msg (Any): 参数 msg

        Returns:
            None: 无返回值
        """
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
        """注销所有 ROS 订阅并清空相机缓存

        Args:
            None: 无输入参数

        Returns:
            None: 无返回值
        """
        for cache in self.cameras.values():
            if cache.image_sub is not None:
                cache.image_sub.unregister()
            if cache.info_sub is not None:
                cache.info_sub.unregister()
        self.cameras.clear()
