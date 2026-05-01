from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from PySide6.QtCore import QCoreApplication, QObject, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider

from hand_eye_calibrator.core.io import read_data, write_data
from hand_eye_calibrator.core.transform import make_transform, quaternion_xyzw_to_matrix
from hand_eye_calibrator.dataset.loader import load_dataset_records
from hand_eye_calibrator.dataset.schema import CalibrationTask
from hand_eye_calibrator.report.exporter import export_result, export_tf_bundle
from hand_eye_calibrator.ros.tf_reader import TfReader
from hand_eye_calibrator.ros.topic_reader import RosTopicReader

DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "default.yaml"
QML_MAIN = Path(__file__).resolve().parent / "qml" / "Main.qml"


def _json(payload) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _loads(raw: str) -> dict:
    return json.loads(raw) if raw else {}


class CameraImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self._image = QImage()

    def set_bgr(self, frame) -> None:
        if frame is None:
            self._image = QImage()
            return
        rgb = np.ascontiguousarray(frame[:, :, ::-1])
        h, w = rgb.shape[:2]
        image = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)
        self._image = image.copy()

    def requestImage(self, image_id, size, requested_size):  # noqa: N802 - Qt API
        if self._image.isNull():
            fallback = QImage(1280, 720, QImage.Format_RGB32)
            fallback.fill(0x172033)
            return fallback
        return self._image


class CalibratorBackend(QObject):
    logChanged = Signal(str)
    stateChanged = Signal(str)
    imageChanged = Signal(str)
    previewStatusChanged = Signal(str)

    def __init__(self, image_provider: CameraImageProvider):
        super().__init__()
        self.image_provider = image_provider
        self.config_path = DEFAULT_CONFIG
        self.cfg = read_data(DEFAULT_CONFIG)
        self.ros_reader: Optional[RosTopicReader] = None
        self.tf_reader: Optional[TfReader] = None
        self.results = []
        self.preview_camera = "wrist"
        self.image_revision = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        if QCoreApplication.instance() is not None:
            self.timer.start(90)

    @Slot(result=str)
    def initialState(self) -> str:
        project = self.cfg.get("project", {})
        robot = self.cfg.get("robot", {})
        board = self.cfg.get("board", {})
        cameras = self.cfg.get("cameras", {})
        return _json(
            {
                "configPath": str(self.config_path),
                "projectName": project.get(
                    "name", "multifunction_hand_eye_calibration"
                ),
                "datasetRoot": project.get(
                    "dataset_root", "./datasets/hand_eye_calibration"
                ),
                "outputRoot": project.get("output_root", "./outputs"),
                "baseFrame": robot.get("base_frame", "base_link"),
                "toolFrame": robot.get("tool_frame", "link_tcp"),
                "tfTimeout": str(robot.get("tf_timeout_sec", 0.3)),
                "boardType": board.get("type", "charuco"),
                "chessCols": int(board.get("cols", 9)),
                "chessRows": int(board.get("rows", 6)),
                "squareSize": str(
                    board.get("square_size_m", board.get("square_length_m", 0.030))
                ),
                "charucoX": int(board.get("squares_x", 8)),
                "charucoY": int(board.get("squares_y", 11)),
                "markerLength": str(board.get("marker_length_m", 0.022)),
                "dictionary": board.get("dictionary", "DICT_5X5_100"),
                "fx": "600",
                "fy": "600",
                "cx": "320",
                "cy": "240",
                "dist": "0,0,0,0,0",
                "sampleId": self._next_sample_id(
                    Path(project.get("dataset_root", "./datasets/hand_eye_calibration"))
                ),
                "tasks": self.cfg.get("calibration_tasks", []),
                "cameras": {
                    name: {
                        "imageTopic": payload.get("image_topic", ""),
                        "cameraInfoTopic": payload.get("camera_info_topic", ""),
                        "frameId": payload.get("frame_id", ""),
                        "role": payload.get("role", ""),
                        "status": "未连接",
                    }
                    for name, payload in cameras.items()
                },
            }
        )

    def _state_to_config(self, state: dict) -> dict:
        cameras = {}
        for name, payload in state.get("cameras", {}).items():
            cameras[name] = {
                "image_topic": payload.get("imageTopic", ""),
                "camera_info_topic": payload.get("cameraInfoTopic", ""),
                "frame_id": payload.get("frameId", ""),
                "role": payload.get("role", ""),
            }
        board_type = state.get("boardType", "charuco")
        if board_type == "chessboard":
            board = {
                "type": "chessboard",
                "cols": int(state.get("chessCols", 9)),
                "rows": int(state.get("chessRows", 6)),
                "square_size_m": float(state.get("squareSize", 0.025)),
            }
        else:
            board = {
                "type": "charuco",
                "squares_x": int(state.get("charucoX", 8)),
                "squares_y": int(state.get("charucoY", 11)),
                "square_length_m": float(state.get("squareSize", 0.030)),
                "marker_length_m": float(state.get("markerLength", 0.022)),
                "dictionary": state.get("dictionary", "DICT_5X5_100"),
            }
        return {
            "project": {
                "name": state.get("projectName", "multifunction_hand_eye_calibration"),
                "dataset_root": state.get(
                    "datasetRoot", "./datasets/hand_eye_calibration"
                ),
                "output_root": state.get("outputRoot", "./outputs"),
            },
            "robot": {
                "base_frame": state.get("baseFrame", "base_link"),
                "tool_frame": state.get("toolFrame", "link_tcp"),
                "tf_timeout_sec": float(state.get("tfTimeout", 0.3)),
            },
            "cameras": cameras,
            "board": board,
            "calibration_tasks": self.cfg.get("calibration_tasks", []),
        }

    def _next_sample_id(self, dataset_root: Path) -> int:
        samples_root = dataset_root / "samples"
        if not samples_root.exists():
            return 1
        ids = [
            int(p.name)
            for p in samples_root.iterdir()
            if p.is_dir() and p.name.isdigit()
        ]
        return max(ids, default=0) + 1

    @Slot(str)
    def saveConfig(self, raw_state: str) -> None:
        state = _loads(raw_state)
        self.cfg = self._state_to_config(state)
        self.config_path = Path(state.get("configPath") or self.config_path)
        write_data(self.config_path, self.cfg)
        self.logChanged.emit(f"配置已保存: {self.config_path}")

    @Slot(str)
    def loadConfig(self, path: str) -> None:
        self.config_path = Path(path) if path else self.config_path
        self.cfg = read_data(self.config_path)
        self.stateChanged.emit(self.initialState())
        self.logChanged.emit(f"配置已加载: {self.config_path}")

    @Slot(str)
    def connectRos(self, raw_state: str) -> None:
        try:
            state = _loads(raw_state)
            self.cfg = self._state_to_config(state)
            if self.ros_reader is not None:
                self.ros_reader.shutdown()
            self.ros_reader = RosTopicReader()
            for name, payload in self.cfg.get("cameras", {}).items():
                self.ros_reader.connect_camera(
                    name,
                    payload.get("image_topic", ""),
                    payload.get("camera_info_topic", ""),
                    payload.get("frame_id", ""),
                )
            self.logChanged.emit("ROS 图像与 camera_info 话题已订阅")
            self.previewStatusChanged.emit("ROS 已连接，等待图像帧")
        except Exception as exc:
            self.logChanged.emit(f"ROS 连接失败: {exc}")
            self.previewStatusChanged.emit("ROS 连接失败")

    @Slot(str)
    def setPreviewCamera(self, name: str) -> None:
        self.preview_camera = name or "wrist"
        self._tick()

    def _tick(self) -> None:
        if self.ros_reader is None:
            return
        cache = self.ros_reader.cameras.get(self.preview_camera)
        if cache is None:
            return
        if cache.last_cv_image is None:
            self.previewStatusChanged.emit(f"{self.preview_camera}: 等待图像")
            return
        self.image_provider.set_bgr(cache.last_cv_image)
        self.image_revision += 1
        self.imageChanged.emit(f"image://camera/preview?rev={self.image_revision}")
        self.previewStatusChanged.emit(f"{self.preview_camera}: live")

    def _task(self, state: dict) -> CalibrationTask:
        task_name = state.get("activeTask", "")
        task_payload = next(
            (
                task
                for task in self.cfg.get("calibration_tasks", [])
                if task.get("name") == task_name
            ),
            self.cfg.get("calibration_tasks", [{}])[0],
        )
        return CalibrationTask(
            name=task_payload["name"],
            type=task_payload["type"],
            camera=task_payload.get("camera"),
            reference_camera=task_payload.get("reference_camera"),
            target_camera=task_payload.get("target_camera"),
            output_parent=task_payload["output_parent"],
            output_child=task_payload["output_child"],
        )

    def _task_camera_names(self, task: CalibrationTask) -> List[str]:
        if task.type == "camera_to_camera":
            return [task.reference_camera, task.target_camera]
        return [task.camera]

    def _board_config(self, state: dict) -> dict:
        return self._state_to_config(state)["board"]

    def _camera_matrix(self, state: dict) -> np.ndarray:
        return np.array(
            [
                [float(state.get("fx", 600)), 0.0, float(state.get("cx", 320))],
                [0.0, float(state.get("fy", 600)), float(state.get("cy", 240))],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

    def _dist_coeffs(self, state: dict) -> np.ndarray:
        return np.array(
            [
                float(v.strip())
                for v in str(state.get("dist", "0,0,0,0,0")).split(",")
                if v.strip()
            ],
            dtype=np.float64,
        )

    def _detect_for_camera(self, state: dict, name: str):
        if self.ros_reader is None or name not in self.ros_reader.cameras:
            raise RuntimeError(f"相机未连接: {name}")
        cache = self.ros_reader.cameras[name]
        if cache.last_cv_image is None:
            raise RuntimeError(f"相机暂无图像: {name}")
        K = self._camera_matrix(state)
        D = self._dist_coeffs(state)
        if cache.last_camera_info and cache.last_camera_info.get("K"):
            K = np.array(cache.last_camera_info["K"], dtype=np.float64).reshape(3, 3)
            D = np.array(cache.last_camera_info.get("D", D), dtype=np.float64)
        from hand_eye_calibrator.boards import create_board_detector

        detector = create_board_detector(self._board_config(state))
        obs = detector.detect(cache.last_cv_image, K, D)
        return cache, obs

    @Slot(str)
    def testDetection(self, raw_state: str) -> None:
        try:
            state = _loads(raw_state)
            name = state.get("previewCamera", self.preview_camera)
            _, obs = self._detect_for_camera(state, name)
            if obs.annotated_image is not None:
                self.image_provider.set_bgr(obs.annotated_image)
                self.image_revision += 1
                self.imageChanged.emit(
                    f"image://camera/preview?rev={self.image_revision}"
                )
            self.logChanged.emit(
                f"{name} 检测: ok={obs.ok}, corners={obs.corners_count}, reproj={obs.reprojection_error_px}"
            )
        except Exception as exc:
            self.logChanged.emit(f"检测失败: {exc}")

    @Slot(str, result=str)
    def refreshTf(self, raw_state: str) -> str:
        try:
            state = _loads(raw_state)
            if self.tf_reader is None:
                self.tf_reader = TfReader()
            T = self.tf_reader.lookup(
                state.get("baseFrame", "base_link"),
                state.get("toolFrame", "link_tcp"),
                float(state.get("tfTimeout", 0.3)),
            )
            text = np.array2string(T, precision=4, suppress_small=True)
            self.logChanged.emit("TF 查询成功")
            return text
        except Exception as exc:
            self.logChanged.emit(f"TF 查询失败: {exc}")
            return str(exc)

    @Slot(str, result=int)
    def captureSample(self, raw_state: str) -> int:
        try:
            state = _loads(raw_state)
            self.cfg = self._state_to_config(state)
            task = self._task(state)
            names = [name for name in self._task_camera_names(task) if name]
            camera_payloads: Dict[str, dict] = {}
            stamps = []
            for name in names:
                cache, obs = self._detect_for_camera(state, name)
                if cache.last_stamp_sec is not None:
                    stamps.append(cache.last_stamp_sec)
                camera_payloads[name] = {
                    "image": cache.last_cv_image.copy(),
                    "camera_info": cache.last_camera_info,
                    "observation": obs,
                }
            T_base_tool = None
            if task.type != "camera_to_camera":
                if self.tf_reader is None:
                    self.tf_reader = TfReader()
                T_base_tool = self.tf_reader.lookup(
                    state.get("baseFrame", "base_link"),
                    state.get("toolFrame", "link_tcp"),
                    float(state.get("tfTimeout", 0.3)),
                )
            max_delta_ms = (
                (max(stamps) - min(stamps)) * 1000.0 if len(stamps) > 1 else 0.0
            )
            sample_id = int(state.get("sampleId", 1))
            from hand_eye_calibrator.dataset.writer import write_sample

            sample_dir = write_sample(
                Path(state.get("datasetRoot", "./datasets/hand_eye_calibration")),
                sample_id,
                camera_payloads,
                T_base_tool=T_base_tool,
                used_for=[task.name],
                sync_payload={"max_camera_delta_ms": max_delta_ms},
            )
            ok_summary = ", ".join(
                f"{name}:{payload['observation'].ok}"
                for name, payload in camera_payloads.items()
            )
            self.logChanged.emit(f"样本 {sample_dir.name} 已保存: {ok_summary}")
            return sample_id + 1
        except Exception as exc:
            self.logChanged.emit(f"采样失败: {exc}")
            return int(_loads(raw_state).get("sampleId", 1))

    def _parse_T_tool_board(self, state: dict):
        raw = [
            float(v.strip())
            for v in str(state.get("tToolBoard", "0,0,0,0,0,0,1")).split(",")
            if v.strip()
        ]
        if len(raw) != 7:
            raise ValueError("T_tool_board 必须是 x,y,z,qx,qy,qz,qw")
        return make_transform(quaternion_xyzw_to_matrix(raw[3:]), raw[:3])

    @Slot(str, result=str)
    def runCalibration(self, raw_state: str) -> str:
        try:
            state = _loads(raw_state)
            self.cfg = self._state_to_config(state)
            task = self._task(state)
            min_id = int(state.get("minId", 0)) or None
            max_id = int(state.get("maxId", 0)) or None
            records = load_dataset_records(
                Path(state.get("datasetRoot", "./datasets/hand_eye_calibration")),
                list(self.cfg.get("cameras", {}).keys()),
                min_id,
                max_id,
            )
            kwargs = {}
            if task.type == "eye_in_hand":
                kwargs["method"] = state.get("method", "TSAI")
            if task.type in ("eye_to_hand", "eye_to_hand_known_board"):
                kwargs["T_tool_board"] = self._parse_T_tool_board(state)
            from hand_eye_calibrator.solvers import create_solver

            result = create_solver(task.type, **kwargs).solve(task, records)
            out = export_result(Path(state.get("outputRoot", "./outputs")), result)
            self.results.append(result)
            payload = result.to_payload()
            payload["output_dir"] = str(out)
            self.logChanged.emit(f"标定完成: {task.name}, 输出 {out}")
            return json.dumps(payload, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.logChanged.emit(f"标定失败: {exc}")
            return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)

    @Slot(str)
    def exportTf(self, raw_state: str) -> None:
        try:
            state = _loads(raw_state)
            if not self.results:
                raise RuntimeError("当前 GUI 会话里没有可导出的标定结果")
            out = export_tf_bundle(
                Path(state.get("outputRoot", "./outputs")),
                state.get("projectName", "multifunction_hand_eye_calibration"),
                self.results,
            )
            self.logChanged.emit(f"TF bundle 已导出: {out}")
        except Exception as exc:
            self.logChanged.emit(f"TF 导出失败: {exc}")


def main() -> None:
    app = QGuiApplication(sys.argv)
    image_provider = CameraImageProvider()
    backend = CalibratorBackend(image_provider)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("camera", image_provider)
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(QML_MAIN)))
    if not engine.rootObjects():
        raise SystemExit("failed to load QML GUI")
    raise SystemExit(app.exec())
