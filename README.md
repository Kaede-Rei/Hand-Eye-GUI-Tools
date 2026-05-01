<div align="center">

# Hand-Eye/Cam-Cam Calibration GUI Tools

面向机器人多相机系统的 ROS Noetic 多模式外参标定工作区；本仓库提供了一套基于 **Qt 开发的图形工具（GUI）**，专注于简化复杂的标定流程

![ROS](https://img.shields.io/badge/ROS-Noetic-22314E?logo=ros)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python)
![Qt](https://img.shields.io/badge/GUI-Qt-41CD52?logo=qt)
![OpenCV](https://img.shields.io/badge/Computer_Vision-OpenCV-5C3EE8?logo=opencv)
![Platform](https://img.shields.io/badge/Platform-Ubuntu%2020.04-E95420?logo=ubuntu)
![Catkin](https://img.shields.io/badge/Build-catkin-2F74C0)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

这套 **标定 GUI** 面向机器人多相机外参标定，重点支持三类常见任务：
- **眼在手上 (Eye-in-Hand)**：求解机械臂末端与末端相机之间的位姿变换
- **眼在手外 (Eye-to-Hand)**：求解机械臂基座与外部固定相机之间的位姿变换
- **相机间 (Camera-to-Camera)**：求解多相机系统中不同相机之间的相对位姿变换

项目支持多相机统一配置、ROS 图像与 `camera_info` 订阅、TF 查询、标定板检测、样本数据集管理、三类外参求解、报告生成和 static TF 导出。GUI 基于 Qt 实现，目标是在一个工作台中完成采集、检测、求解和交付。

当前工具覆盖腕上相机、外部相机和相机到相机的统一标定链路；采集侧订阅 ROS image / camera_info / TF，求解侧统一使用 `T_A_B` 变换约定，最终输出可直接接入 TF tree 的静态外参，同时包含标定板检测、数据集管理等实用功能

## 标定目标

```text
base_link
├── mid_camera_color_optical_frame
│   └── far_camera_color_optical_frame
└── link_tcp
    └── wrist_camera_color_optical_frame
```

| 任务 | 类型 | 输入 | 输出 |
|---|---|---|---|
| `wrist_eye_in_hand` | `eye_in_hand` | wrist 图像、camera_info、`base_link -> link_tcp` TF | `link_tcp -> wrist_camera_color_optical_frame` |
| `mid_eye_to_hand` | `eye_to_hand_known_board` | mid 图像、camera_info、`base_link -> link_tcp` TF、已知 `T_tool_board` | `base_link -> mid_camera_color_optical_frame` |
| `far_to_mid` | `camera_to_camera` | mid / far 同步图像、camera_info、共同标定板检测 | `mid_camera_color_optical_frame -> far_camera_color_optical_frame` |

## 包结构

```text
hand-eye-ws/
├── README.md
├── plan.md
└── src/
    └── hand_eye_calibrator/
        ├── config/
        ├── scripts/
        └── src/hand_eye_calibrator/
            ├── boards/                   # ChessBoard / ChArUco 检测
            ├── core/                     # 变换、四元数、IO、重投影误差
            ├── dataset/                  # 数据集 schema、加载与写入
            ├── gui/                      # Qt GUI 模块
            ├── report/                   # YAML、Markdown、static TF 导出
            ├── ros/                      # ROS topic 与 TF 适配
            └── solvers/                  # 三类外参求解器
```

核心模块职责：

| 模块 | 作用 |
|---|---|
| `boards` | 统一 `BoardObservation` 输出，支持 ChessBoard 与 ChArUco |
| `core` | 提供 `make_transform`、`invert_transform`、四元数平均和误差统计 |
| `dataset` | 保存和读取 `samples/<id>/<camera>/` 数据结构 |
| `ros` | 缓存多相机图像、camera_info，查询 `tf2` 变换 |
| `solvers` | 实现 `eye_in_hand`、`eye_to_hand_known_board`、`camera_to_camera` |
| `report` | 导出结果 YAML、报告和静态 TF 启动文件 |
| `gui` | 通过 Qt 后端和前端提供采集、检测、标定和导出界面 |

## 环境

工作区面向 ROS Noetic，推荐使用项目机器上的 `mamba-usb rosnoetic` 环境：

```bash
mamba-usb rosnoetic
```

环境应至少提供：

```bash
python -c "import rospy, cv2"
which catkin_make
```

Python 运行时依赖：

| 依赖 | 用途 |
|---|---|
| `rospy` | ROS Python 节点、topic 订阅 |
| `tf2_ros` | TF 查询 |
| `sensor_msgs` | Image / CameraInfo 消息 |
| `cv_bridge` | ROS Image 转 OpenCV 图像 |
| `opencv-python` 或 ROS OpenCV | 棋盘格、PnP、hand-eye 求解 |
| `opencv-contrib-python` 或带 `aruco` 的 ROS OpenCV | ChArUco 检测 |
| Qt Python 绑定 | 图形用户界面开发 |
| `numpy` | 矩阵计算 |
| `PyYAML` | YAML 配置和数据集 |

## 构建

```bash
cd /path/to/hand-eye-ws
mamba-usb rosnoetic
catkin_make -DCATKIN_ENABLE_TESTING=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
source devel/setup.bash
```

## 启动 GUI

通过 ROS 包入口启动：

```bash
rosrun hand_eye_calibrator multicam_calibrator_gui.py
```

直接从源码启动：

```bash
python3 src/hand_eye_calibrator/scripts/multicam_calibrator_gui.py
```

GUI 页面：

| 页面 | 作用 |
|---|---|
| 项目 | 设置项目名、数据集目录、输出目录和配置文件 |
| 相机 | 配置 wrist / mid / far 三路图像话题、camera_info 话题和 frame_id |
| 标定板 | 设置 ChessBoard / ChArUco 参数和备用相机内参 |
| 机器人 / TF | 检查 `base_frame -> tool_frame` TF 是否可查询 |
| 任务 | 选择当前采样和标定任务 |
| 采样 | 保存当前任务需要的图像、检测结果和机器人位姿 |
| 标定 / 报告 | 运行求解器、查看结果、导出 TF |

## 数据集格式

```text
datasets/hand_eye_calibration/
├── meta.yaml
├── cameras.yaml
├── board.yaml
└── samples/
    └── 000001/
        ├── sample.yaml
        ├── robot_pose.yaml
        ├── wrist/
        │   ├── image.png
        │   ├── camera_info.yaml
        │   ├── detection.yaml
        │   └── annotated.png
        ├── mid/
        └── far/
```

## 命令行标定

运行 wrist eye-in-hand：

```bash
rosrun hand_eye_calibrator run_calibration.py \
  --config src/hand_eye_calibrator/config/default.yaml \
  --task wrist_eye_in_hand
```

运行 mid eye-to-hand 已知板模式：

```bash
rosrun hand_eye_calibrator run_calibration.py \
  --config src/hand_eye_calibrator/config/default.yaml \
  --task mid_eye_to_hand \
  --t-tool-board-yaml ./config/my_tool_board.yaml
```

`T_tool_board` 文件格式：

```yaml
T_tool_board:
  translation: [0.0, 0.0, 0.0]
  rotation_xyzw: [0.0, 0.0, 0.0, 1.0]
```

导出静态 TF：

```bash
rosrun hand_eye_calibrator export_static_tf.py \
  outputs/wrist_eye_in_hand_*/wrist_eye_in_hand.yaml \
  outputs/mid_eye_to_hand_*/mid_eye_to_hand.yaml \
  outputs/far_to_mid_*/far_to_mid.yaml \
  --project hand_eye_calibration
```

## 输出

单任务标定输出：

```text
outputs/<task>_<timestamp>/
├── <task>.yaml
└── report.md
```

TF bundle 输出：

```text
outputs/hand_eye_calibration_tf_<timestamp>/
├── tf_tree.yaml
├── static_tf.launch
├── static_tf.sh
└── report.md
```

`static_tf.launch` 可直接发布：

```bash
roslaunch outputs/hand_eye_calibration_tf_<timestamp>/static_tf.launch
```

## License

MIT. See `src/hand_eye_calibrator/package.xml`.
