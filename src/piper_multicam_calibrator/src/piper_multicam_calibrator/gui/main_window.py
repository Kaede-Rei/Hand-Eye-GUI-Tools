from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from piper_multicam_calibrator.boards import create_board_detector
from piper_multicam_calibrator.core.io import ensure_dir, read_data, write_data
from piper_multicam_calibrator.core.transform import make_transform, quaternion_xyzw_to_matrix, transform_from_dict
from piper_multicam_calibrator.dataset.loader import load_dataset_records
from piper_multicam_calibrator.dataset.schema import CalibrationTask
from piper_multicam_calibrator.dataset.writer import next_sample_id, write_sample
from piper_multicam_calibrator.report.exporter import export_result, export_tf_bundle
from piper_multicam_calibrator.ros.tf_reader import TfReader
from piper_multicam_calibrator.ros.topic_reader import RosTopicReader
from piper_multicam_calibrator.solvers import create_solver


DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "config" / "c1_three_camera.yaml"


class VideoLabel(QLabel):
    def __init__(self):
        super().__init__("No image")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 360)
        self.setStyleSheet("background:#111;color:#ccc;")
        self._image = None

    def set_bgr(self, image):
        self._image = image.copy() if image is not None else None
        self._refresh()

    def resizeEvent(self, event):
        self._refresh()
        super().resizeEvent(event)

    def _refresh(self):
        if self._image is None:
            self.setText("No image")
            return
        rgb = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(pix)


class MulticamCalibratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Piper Multi-Camera Calibrator")
        self.config_path = DEFAULT_CONFIG
        self.cfg = read_data(DEFAULT_CONFIG)
        self.ros_reader = None
        self.tf_reader = None
        self.results = []
        self.camera_rows: Dict[str, dict] = {}
        self._build_ui()
        self._load_cfg_to_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(100)

    def _build_ui(self):
        root = QWidget()
        layout = QHBoxLayout(root)
        self.video = VideoLabel()
        layout.addWidget(self.video, 2)
        side = QVBoxLayout()
        self.tabs = QTabWidget()
        side.addWidget(self.tabs, 3)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(130)
        side.addWidget(self.log_box, 1)
        layout.addLayout(side, 3)
        self.setCentralWidget(root)

        self._build_project_tab()
        self._build_cameras_tab()
        self._build_board_tab()
        self._build_robot_tab()
        self._build_task_tab()
        self._build_capture_tab()
        self._build_calibrate_tab()

    def _wrap(self, widget):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(widget)
        return area

    def _edit(self, text=""):
        edit = QLineEdit(str(text))
        edit.setMinimumWidth(260)
        return edit

    def _build_project_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        self.project_name = self._edit()
        self.dataset_root = self._edit()
        self.output_root = self._edit()
        self.config_file = self._edit(str(DEFAULT_CONFIG))
        row = QHBoxLayout()
        save = QPushButton("保存配置")
        load = QPushButton("加载配置")
        browse = QPushButton("选择配置")
        save.clicked.connect(self.save_config)
        load.clicked.connect(self.load_config)
        browse.clicked.connect(self.browse_config)
        row.addWidget(save)
        row.addWidget(load)
        row.addWidget(browse)
        form.addRow("project name", self.project_name)
        form.addRow("dataset_root", self.dataset_root)
        form.addRow("output_root", self.output_root)
        form.addRow("config", self.config_file)
        form.addRow(row)
        self.tabs.addTab(self._wrap(page), "Project")

    def _build_cameras_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.preview_camera = QComboBox()
        layout.addWidget(QLabel("相机配置"))
        for name in ("wrist", "mid", "far"):
            group = QGroupBox(name)
            form = QFormLayout(group)
            self.camera_rows[name] = {
                "image_topic": self._edit(),
                "camera_info_topic": self._edit(),
                "frame_id": self._edit(),
                "role": self._edit(),
                "status": QLabel("not connected"),
            }
            for key, widget in self.camera_rows[name].items():
                form.addRow(key, widget)
            layout.addWidget(group)
            self.preview_camera.addItem(name)
        connect = QPushButton("连接 ROS 话题")
        connect.clicked.connect(self.connect_ros_topics)
        layout.addWidget(connect)
        layout.addWidget(QLabel("预览相机"))
        layout.addWidget(self.preview_camera)
        self.tabs.addTab(self._wrap(page), "Cameras")

    def _build_board_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        self.board_type = QComboBox()
        self.board_type.addItems(["charuco", "chessboard"])
        self.chess_cols = QSpinBox(); self.chess_cols.setRange(2, 30); self.chess_cols.setValue(9)
        self.chess_rows = QSpinBox(); self.chess_rows.setRange(2, 30); self.chess_rows.setValue(6)
        self.square_size = self._edit("0.025")
        self.charuco_x = QSpinBox(); self.charuco_x.setRange(2, 30); self.charuco_x.setValue(8)
        self.charuco_y = QSpinBox(); self.charuco_y.setRange(2, 30); self.charuco_y.setValue(11)
        self.marker_length = self._edit("0.022")
        self.dictionary = self._edit("DICT_5X5_100")
        self.fx = self._edit("600"); self.fy = self._edit("600")
        self.cx = self._edit("320"); self.cy = self._edit("240")
        self.dist = self._edit("0,0,0,0,0")
        test = QPushButton("测试当前预览检测")
        test.clicked.connect(self.test_detection)
        form.addRow("board_type", self.board_type)
        form.addRow("chess cols", self.chess_cols)
        form.addRow("chess rows", self.chess_rows)
        form.addRow("square_length_m", self.square_size)
        form.addRow("charuco squares_x", self.charuco_x)
        form.addRow("charuco squares_y", self.charuco_y)
        form.addRow("charuco marker_length_m", self.marker_length)
        form.addRow("dictionary", self.dictionary)
        form.addRow("fx", self.fx); form.addRow("fy", self.fy)
        form.addRow("cx", self.cx); form.addRow("cy", self.cy)
        form.addRow("dist coeffs", self.dist)
        form.addRow(test)
        self.tabs.addTab(self._wrap(page), "Board")

    def _build_robot_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        self.base_frame = self._edit("base_link")
        self.tool_frame = self._edit("link_tcp")
        self.tf_timeout = self._edit("0.3")
        self.current_tf = QLabel("not queried")
        refresh = QPushButton("刷新 base->tool TF")
        refresh.clicked.connect(self.refresh_tf)
        form.addRow("base_frame", self.base_frame)
        form.addRow("tool_frame", self.tool_frame)
        form.addRow("tf_timeout_sec", self.tf_timeout)
        form.addRow(refresh)
        form.addRow("current", self.current_tf)
        self.tabs.addTab(self._wrap(page), "Robot / TF")

    def _build_task_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        self.task_combo = QComboBox()
        self.task_combo.currentIndexChanged.connect(self._update_capture_hint)
        form.addRow("active task", self.task_combo)
        self.task_hint = QLabel("")
        self.task_hint.setWordWrap(True)
        form.addRow("needs", self.task_hint)
        self.tabs.addTab(self._wrap(page), "Task")

    def _build_capture_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        self.sample_id = QSpinBox(); self.sample_id.setRange(1, 999999); self.sample_id.setValue(1)
        self.auto_inc = QCheckBox("auto increment"); self.auto_inc.setChecked(True)
        capture = QPushButton("采集当前任务样本")
        capture.clicked.connect(self.capture_sample)
        form.addRow("sample_id", self.sample_id)
        form.addRow(self.auto_inc)
        form.addRow(capture)
        self.capture_status = QLabel("")
        self.capture_status.setWordWrap(True)
        form.addRow("status", self.capture_status)
        self.tabs.addTab(self._wrap(page), "Capture")

    def _build_calibrate_tab(self):
        page = QWidget()
        form = QFormLayout(page)
        self.min_id = QSpinBox(); self.min_id.setRange(0, 999999)
        self.max_id = QSpinBox(); self.max_id.setRange(0, 999999)
        self.method = QComboBox(); self.method.addItems(["TSAI", "PARK", "HORAUD", "ANDREFF", "DANIILIDIS"])
        self.t_tool_board = self._edit("0,0,0,0,0,0,1")
        run = QPushButton("运行当前任务标定")
        export = QPushButton("导出当前结果 TF")
        run.clicked.connect(self.run_calibration)
        export.clicked.connect(self.export_tf)
        form.addRow("min sample id (0=all)", self.min_id)
        form.addRow("max sample id (0=all)", self.max_id)
        form.addRow("eye-in-hand method", self.method)
        form.addRow("T_tool_board x,y,z,qx,qy,qz,qw", self.t_tool_board)
        form.addRow(run)
        form.addRow(export)
        self.result_text = QTextEdit(); self.result_text.setReadOnly(True)
        form.addRow("result", self.result_text)
        self.tabs.addTab(self._wrap(page), "Calibrate / Report")

    def _load_cfg_to_ui(self):
        project = self.cfg.get("project", {})
        self.project_name.setText(project.get("name", "c1_three_camera_calibration"))
        self.dataset_root.setText(project.get("dataset_root", "./datasets/c1_three_camera"))
        self.output_root.setText(project.get("output_root", "./outputs"))
        robot = self.cfg.get("robot", {})
        self.base_frame.setText(robot.get("base_frame", "base_link"))
        self.tool_frame.setText(robot.get("tool_frame", "link_tcp"))
        self.tf_timeout.setText(str(robot.get("tf_timeout_sec", 0.3)))
        for name, payload in self.cfg.get("cameras", {}).items():
            if name in self.camera_rows:
                for key in ("image_topic", "camera_info_topic", "frame_id", "role"):
                    self.camera_rows[name][key].setText(payload.get(key, ""))
        board = self.cfg.get("board", {})
        self.board_type.setCurrentText(board.get("type", "charuco"))
        self.chess_cols.setValue(int(board.get("cols", 9)))
        self.chess_rows.setValue(int(board.get("rows", 6)))
        self.square_size.setText(str(board.get("square_size_m", board.get("square_length_m", 0.030))))
        self.charuco_x.setValue(int(board.get("squares_x", 8)))
        self.charuco_y.setValue(int(board.get("squares_y", 11)))
        self.marker_length.setText(str(board.get("marker_length_m", 0.022)))
        self.dictionary.setText(board.get("dictionary", "DICT_5X5_100"))
        self.task_combo.clear()
        for task in self.cfg.get("calibration_tasks", []):
            self.task_combo.addItem(task["name"], task)
        self.sample_id.setValue(next_sample_id(Path(self.dataset_root.text())))
        self._update_capture_hint()

    def _ui_to_config(self) -> dict:
        cfg = {
            "project": {
                "name": self.project_name.text().strip(),
                "dataset_root": self.dataset_root.text().strip(),
                "output_root": self.output_root.text().strip(),
            },
            "robot": {
                "base_frame": self.base_frame.text().strip(),
                "tool_frame": self.tool_frame.text().strip(),
                "tf_timeout_sec": float(self.tf_timeout.text()),
            },
            "cameras": {},
            "board": self.current_board_config(),
            "calibration_tasks": self.cfg.get("calibration_tasks", []),
        }
        for name, row in self.camera_rows.items():
            cfg["cameras"][name] = {
                "image_topic": row["image_topic"].text().strip(),
                "camera_info_topic": row["camera_info_topic"].text().strip(),
                "frame_id": row["frame_id"].text().strip(),
                "role": row["role"].text().strip(),
            }
        return cfg

    def current_board_config(self) -> dict:
        if self.board_type.currentText() == "chessboard":
            return {
                "type": "chessboard",
                "cols": int(self.chess_cols.value()),
                "rows": int(self.chess_rows.value()),
                "square_size_m": float(self.square_size.text()),
            }
        return {
            "type": "charuco",
            "squares_x": int(self.charuco_x.value()),
            "squares_y": int(self.charuco_y.value()),
            "square_length_m": float(self.square_size.text()),
            "marker_length_m": float(self.marker_length.text()),
            "dictionary": self.dictionary.text().strip(),
        }

    def camera_matrix(self):
        return np.array(
            [[float(self.fx.text()), 0.0, float(self.cx.text())], [0.0, float(self.fy.text()), float(self.cy.text())], [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )

    def dist_coeffs(self):
        return np.array([float(v.strip()) for v in self.dist.text().split(",") if v.strip()], dtype=np.float64)

    def active_task(self) -> CalibrationTask:
        payload = self.task_combo.currentData()
        return CalibrationTask(
            name=payload["name"],
            type=payload["type"],
            camera=payload.get("camera"),
            reference_camera=payload.get("reference_camera"),
            target_camera=payload.get("target_camera"),
            output_parent=payload["output_parent"],
            output_child=payload["output_child"],
        )

    def task_camera_names(self, task: CalibrationTask) -> List[str]:
        if task.type == "camera_to_camera":
            return [task.reference_camera, task.target_camera]
        return [task.camera]

    def browse_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择配置", str(Path.cwd()), "YAML (*.yaml *.yml);;All (*)")
        if path:
            self.config_file.setText(path)

    def load_config(self):
        self.config_path = Path(self.config_file.text())
        self.cfg = read_data(self.config_path)
        self._load_cfg_to_ui()
        self.log(f"loaded config: {self.config_path}")

    def save_config(self):
        self.cfg = self._ui_to_config()
        path = Path(self.config_file.text())
        write_data(path, self.cfg)
        self.log(f"saved config: {path}")

    def connect_ros_topics(self):
        try:
            if self.ros_reader is not None:
                self.ros_reader.shutdown()
            self.ros_reader = RosTopicReader()
            for name, row in self.camera_rows.items():
                self.ros_reader.connect_camera(
                    name,
                    row["image_topic"].text().strip(),
                    row["camera_info_topic"].text().strip(),
                    row["frame_id"].text().strip(),
                )
                row["status"].setText("subscribed")
            self.log("ROS camera topics subscribed")
        except Exception as exc:
            QMessageBox.critical(self, "ROS error", str(exc))
            self.log(f"ROS connect failed: {exc}")

    def refresh_tf(self):
        try:
            if self.tf_reader is None:
                self.tf_reader = TfReader()
            T = self.tf_reader.lookup(self.base_frame.text().strip(), self.tool_frame.text().strip(), float(self.tf_timeout.text()))
            self.current_tf.setText(np.array2string(T, precision=4, suppress_small=True))
            return T
        except Exception as exc:
            self.current_tf.setText(str(exc))
            self.log(f"TF lookup failed: {exc}")
            return None

    def _tick(self):
        if self.ros_reader is None:
            return
        name = self.preview_camera.currentText()
        cache = self.ros_reader.cameras.get(name)
        if cache is not None:
            self.camera_rows[name]["status"].setText("image" if cache.last_cv_image is not None else "waiting")
            if cache.last_cv_image is not None:
                self.video.set_bgr(cache.last_cv_image)

    def _update_capture_hint(self):
        if self.task_combo.count() == 0:
            return
        task = self.active_task()
        if task.type == "camera_to_camera":
            text = f"需要 {task.reference_camera} + {task.target_camera} 图像、camera_info、同一标定板检测。"
        else:
            text = f"需要 {task.camera} 图像、camera_info、{self.base_frame.text()}->{self.tool_frame.text()} TF、标定板检测。"
        self.task_hint.setText(text)

    def _detect_for_camera(self, name: str):
        if self.ros_reader is None or name not in self.ros_reader.cameras:
            raise RuntimeError(f"camera {name} is not connected")
        cache = self.ros_reader.cameras[name]
        if cache.last_cv_image is None:
            raise RuntimeError(f"camera {name} has no image")
        K = self.camera_matrix()
        D = self.dist_coeffs()
        if cache.last_camera_info and cache.last_camera_info.get("K"):
            K = np.array(cache.last_camera_info["K"], dtype=np.float64).reshape(3, 3)
            D = np.array(cache.last_camera_info.get("D", D), dtype=np.float64)
        detector = create_board_detector(self.current_board_config())
        obs = detector.detect(cache.last_cv_image, K, D)
        return cache, obs

    def test_detection(self):
        try:
            name = self.preview_camera.currentText()
            _, obs = self._detect_for_camera(name)
            if obs.annotated_image is not None:
                self.video.set_bgr(obs.annotated_image)
            self.log(f"{name} detection: ok={obs.ok}, corners={obs.corners_count}, reproj={obs.reprojection_error_px}")
        except Exception as exc:
            QMessageBox.critical(self, "Detection error", str(exc))
            self.log(f"detection failed: {exc}")

    def capture_sample(self):
        try:
            task = self.active_task()
            names = [n for n in self.task_camera_names(task) if n]
            camera_payloads = {}
            stamps = []
            for name in names:
                cache, obs = self._detect_for_camera(name)
                if cache.last_stamp_sec is not None:
                    stamps.append(cache.last_stamp_sec)
                camera_payloads[name] = {
                    "image": cache.last_cv_image.copy(),
                    "camera_info": cache.last_camera_info,
                    "observation": obs,
                }
            T_base_tool = None if task.type == "camera_to_camera" else self.refresh_tf()
            if task.type != "camera_to_camera" and T_base_tool is None:
                raise RuntimeError("TF base->tool is required for this task")
            max_delta_ms = (max(stamps) - min(stamps)) * 1000.0 if len(stamps) > 1 else 0.0
            sample_dir = write_sample(
                Path(self.dataset_root.text()),
                int(self.sample_id.value()),
                camera_payloads,
                T_base_tool=T_base_tool,
                used_for=[task.name],
                sync_payload={"max_camera_delta_ms": max_delta_ms},
            )
            ok_summary = ", ".join(f"{n}:{p['observation'].ok}" for n, p in camera_payloads.items())
            self.capture_status.setText(f"saved {sample_dir}; {ok_summary}")
            self.log(f"saved sample {sample_dir.name}: {ok_summary}")
            if self.auto_inc.isChecked():
                self.sample_id.setValue(self.sample_id.value() + 1)
        except Exception as exc:
            QMessageBox.critical(self, "Capture error", str(exc))
            self.log(f"capture failed: {exc}")

    def _parse_T_tool_board(self):
        raw = [float(v.strip()) for v in self.t_tool_board.text().split(",") if v.strip()]
        if len(raw) != 7:
            raise ValueError("T_tool_board must be x,y,z,qx,qy,qz,qw")
        return make_transform(quaternion_xyzw_to_matrix(raw[3:]), raw[:3])

    def run_calibration(self):
        try:
            task = self.active_task()
            min_id = self.min_id.value() or None
            max_id = self.max_id.value() or None
            records = load_dataset_records(Path(self.dataset_root.text()), list(self.camera_rows.keys()), min_id, max_id)
            kwargs = {}
            if task.type == "eye_in_hand":
                kwargs["method"] = self.method.currentText()
            if task.type in ("eye_to_hand", "eye_to_hand_known_board"):
                kwargs["T_tool_board"] = self._parse_T_tool_board()
            result = create_solver(task.type, **kwargs).solve(task, records)
            out = export_result(Path(self.output_root.text()), result)
            self.results.append(result)
            self.result_text.setText(str(result.to_payload()))
            self.log(f"calibration done: {task.name}, output={out}")
        except Exception as exc:
            QMessageBox.critical(self, "Calibration error", str(exc))
            self.log(f"calibration failed: {exc}")

    def export_tf(self):
        try:
            if not self.results:
                raise RuntimeError("no calibration results in this GUI session")
            out = export_tf_bundle(Path(self.output_root.text()), self.project_name.text().strip(), self.results)
            self.log(f"TF bundle exported: {out}")
        except Exception as exc:
            QMessageBox.critical(self, "Export error", str(exc))
            self.log(f"export failed: {exc}")

    def log(self, message: str):
        self.log_box.append(message)


def main():
    app = QApplication([])
    window = MulticamCalibratorWindow()
    window.showMaximized()
    app.exec_()
