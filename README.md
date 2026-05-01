# Piper Multi-Camera Calibrator

面向 C1 三相机系统的 ROS Noetic 多模式外参标定工作区；仓库提供 PyQt5 图形工具、标定板检测、数据集管理、三类外参求解器和静态 TF 导出入口

当前工具以 `piper_multicam_calibrator` 为核心包，覆盖腕上近景相机、中景外部相机和外景相机的统一标定链路；采集侧订阅 ROS image / camera_info / TF，求解侧统一使用 `T_A_B` 变换约定，最终输出可直接接入 TF tree 的静态外参

## 标定目标

```text
base_link
├── mid_camera_color_optical_frame
│   └── far_camera_color_optical_frame
└── link_tcp
    └── wrist_camera_color_optical_frame
```

核心任务：

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
    └── piper_multicam_calibrator/
        ├── CMakeLists.txt
        ├── package.xml
        ├── setup.py
        ├── config/
        │   ├── c1_three_camera.yaml
        │   ├── board_chessboard.yaml
        │   └── board_charuco.yaml
        ├── scripts/
        │   ├── multicam_calibrator_gui.py
        │   ├── run_calibration.py
        │   ├── export_static_tf.py
        │   ├── validate_tf.py
        │   └── collect_dataset_node.py
        └── src/piper_multicam_calibrator/
            ├── boards/                   # ChessBoard / ChArUco 检测
            ├── core/                     # 变换、四元数、IO、重投影误差
            ├── dataset/                  # 数据集 schema、加载与写入
            ├── gui/                      # PyQt5 GUI
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
| `gui` | 提供多页式图形采集、检测、标定和导出界面 |

## 环境

工作区面向 ROS Noetic：

环境应至少提供：

```bash
python -c "import rospy, cv2, PyQt5"
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
| `PyQt5` | GUI |
| `numpy` | 矩阵计算 |
| `PyYAML` | YAML 配置和数据集 |

## 构建

```bash
cd /path/to/hand-eye-ws
catkin_make -DCATKIN_ENABLE_TESTING=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
source devel/setup.bash
```

## 启动 GUI

通过 ROS 包入口启动：

```bash
rosrun piper_multicam_calibrator multicam_calibrator_gui.py
```

直接从源码启动：

```bash
python3 src/piper_multicam_calibrator/scripts/multicam_calibrator_gui.py
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
datasets/c1_three_camera/
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
        │   ├── image.png
        │   ├── camera_info.yaml
        │   ├── detection.yaml
        │   └── annotated.png
        └── far/
            ├── image.png
            ├── camera_info.yaml
            ├── detection.yaml
            └── annotated.png
```

`sample.yaml` 记录样本编号、时间戳、任务名、有效相机和时间同步信息；`robot_pose.yaml` 记录 `T_base_tool`；每个相机目录保存原图、内参、检测结果和角点可视化

## 配置

默认配置位于：

```text
src/piper_multicam_calibrator/config/c1_three_camera.yaml
```

相机配置示例：

```yaml
cameras:
  wrist:
    image_topic: /wrist_camera/color/image_raw
    camera_info_topic: /wrist_camera/color/camera_info
    frame_id: wrist_camera_color_optical_frame
    role: wrist_eye_in_hand
```

任务配置示例：

```yaml
calibration_tasks:
  - name: far_to_mid
    type: camera_to_camera
    reference_camera: mid
    target_camera: far
    output_parent: mid_camera_color_optical_frame
    output_child: far_camera_color_optical_frame
```

## 命令行标定

运行 wrist eye-in-hand：

```bash
rosrun piper_multicam_calibrator run_calibration.py \
  --config src/piper_multicam_calibrator/config/c1_three_camera.yaml \
  --task wrist_eye_in_hand
```

运行 mid eye-to-hand 已知板模式：

```bash
rosrun piper_multicam_calibrator run_calibration.py \
  --config src/piper_multicam_calibrator/config/c1_three_camera.yaml \
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
rosrun piper_multicam_calibrator export_static_tf.py \
  outputs/wrist_eye_in_hand_*/wrist_eye_in_hand.yaml \
  outputs/mid_eye_to_hand_*/mid_eye_to_hand.yaml \
  outputs/far_to_mid_*/far_to_mid.yaml \
  --project c1_three_camera
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
outputs/c1_three_camera_tf_<timestamp>/
├── c1_tf_tree.yaml
├── static_tf.launch
├── static_tf.sh
└── report.md
```

`static_tf.launch` 可直接发布：

```bash
roslaunch outputs/c1_three_camera_tf_<timestamp>/static_tf.launch
```
