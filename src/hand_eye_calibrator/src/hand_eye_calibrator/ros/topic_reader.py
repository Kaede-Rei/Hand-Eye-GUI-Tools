from __future__ import annotations

import time
from typing import Dict

import numpy as np

from hand_eye_calibrator.ros.camera_cache import CameraCache


class RosTopicReader:
    IMAGE_BUFF_SIZE = 8 * 1024 * 1024
    BACKGROUND_CONVERT_PERIOD_SEC = 0.5

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
        except Exception as exc:
            raise RuntimeError(f"ROS image dependencies are unavailable: {exc}")
        self.rospy = rospy
        self.Image = Image
        self.CameraInfo = CameraInfo
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
            buff_size=self.IMAGE_BUFF_SIZE,
            tcp_nodelay=True,
        )
        cache.info_sub = self.rospy.Subscriber(
            camera_info_topic,
            self.CameraInfo,
            lambda msg, n=name: self._on_info(n, msg),
            queue_size=1,
        )
        self.cameras[name] = cache
        return cache

    def set_preview_camera(self, name: str) -> None:
        """Mark the camera that should be converted at full preview rate."""
        for camera_name, cache in self.cameras.items():
            cache.needs_preview = camera_name == name
            if cache.needs_preview:
                cache.last_preview_convert_sec = None

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
        receive_sec = self.rospy.Time.now().to_sec()
        convert_started = time.monotonic()
        stamp_sec = self._stamp_sec(msg)
        cache.last_image_msg = msg
        cache.last_stamp_sec = stamp_sec
        cache.last_receive_sec = receive_sec
        should_convert = cache.needs_preview
        if not should_convert:
            last_convert = cache.last_preview_convert_sec
            should_convert = (
                last_convert is None
                or convert_started - last_convert >= self.BACKGROUND_CONVERT_PERIOD_SEC
            )
        if should_convert:
            cache.last_cv_image = self._image_msg_to_bgr(msg)
            cache.last_preview_convert_sec = convert_started
            cache.last_convert_ms = (time.monotonic() - convert_started) * 1000.0
        cache.last_input_latency_ms = max(0.0, (receive_sec - stamp_sec) * 1000.0)
        self._mark_input_frame(cache)

    def _mark_input_frame(self, cache: CameraCache) -> None:
        """Update FPS from frames received and converted by the ROS subscriber."""
        now = time.monotonic()
        if cache.input_fps_started is None:
            cache.input_fps_started = now
            cache.input_fps_frames = 0
        cache.input_fps_frames += 1
        elapsed = now - cache.input_fps_started
        if elapsed < 1.0:
            return
        cache.input_fps = cache.input_fps_frames / elapsed
        cache.input_fps_started = now
        cache.input_fps_frames = 0

    def _image_msg_to_bgr(self, msg) -> np.ndarray:
        """Convert common ROS Image encodings to a BGR uint8 image.

        This intentionally avoids cv_bridge. In the portable micromamba Noetic
        environment cv_bridge imports cv2, which can load an incompatible
        libgobject before the GUI has a chance to subscribe to topics.
        """
        encoding = (msg.encoding or "").lower()
        channels_by_encoding = {
            "bgr8": (np.uint8, 3),
            "rgb8": (np.uint8, 3),
            "bgra8": (np.uint8, 4),
            "rgba8": (np.uint8, 4),
            "mono8": (np.uint8, 1),
            "8uc1": (np.uint8, 1),
            "mono16": (np.uint16, 1),
            "16uc1": (np.uint16, 1),
            "32fc1": (np.float32, 1),
        }
        if encoding not in channels_by_encoding:
            raise RuntimeError(f"Unsupported image encoding: {msg.encoding}")

        dtype, channels = channels_by_encoding[encoding]
        array = np.frombuffer(msg.data, dtype=dtype)
        if msg.is_bigendian and array.dtype.byteorder != ">":
            array = array.byteswap().newbyteorder()

        expected_step = int(msg.width) * channels * np.dtype(dtype).itemsize
        if int(msg.step) < expected_step:
            raise RuntimeError(
                f"Invalid image step {msg.step} for {msg.width}x{msg.height} {msg.encoding}"
            )

        row_items = int(msg.step) // np.dtype(dtype).itemsize
        image = array.reshape((int(msg.height), row_items))
        image = image[:, : int(msg.width) * channels]
        if channels > 1:
            image = image.reshape((int(msg.height), int(msg.width), channels))

        if encoding == "bgr8":
            return np.ascontiguousarray(image)
        if encoding == "rgb8":
            return np.ascontiguousarray(image[:, :, ::-1])
        if encoding == "bgra8":
            return np.ascontiguousarray(image[:, :, :3])
        if encoding == "rgba8":
            return np.ascontiguousarray(image[:, :, [2, 1, 0]])

        mono = self._mono_to_uint8(image)
        return np.ascontiguousarray(np.repeat(mono[:, :, None], 3, axis=2))

    def _mono_to_uint8(self, image: np.ndarray) -> np.ndarray:
        """Scale mono/depth images to uint8 for preview."""
        if image.dtype == np.uint8:
            return image
        if np.issubdtype(image.dtype, np.floating):
            finite = image[np.isfinite(image)]
        else:
            finite = image
        if finite.size == 0:
            return np.zeros(image.shape, dtype=np.uint8)
        low = float(np.nanmin(finite))
        high = float(np.nanmax(finite))
        if high <= low:
            return np.zeros(image.shape, dtype=np.uint8)
        scaled = (image.astype(np.float32) - low) * (255.0 / (high - low))
        return (
            np.nan_to_num(scaled, nan=0.0, posinf=255.0, neginf=0.0)
            .clip(0, 255)
            .astype(np.uint8)
        )

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
