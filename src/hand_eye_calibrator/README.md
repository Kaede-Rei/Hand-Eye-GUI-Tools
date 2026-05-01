# 多功能手眼标定工具 ROS 包

This ROS Noetic package provides the multi-function hand-eye calibration GUI and
solver backend.

## GUI Stack

The GUI is implemented with PySide6 + QML. Python exposes the ROS, dataset and
solver backend as a QObject bridge; QML owns the visual layout, animation,
glass-style panels and interaction states.

## Run

```bash
mamba-usb rosnoetic
catkin_make -DCATKIN_ENABLE_TESTING=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
source devel/setup.bash
rosrun hand_eye_calibrator multicam_calibrator_gui.py
```

Direct source launch:

```bash
mamba-usb rosnoetic
python3 src/hand_eye_calibrator/scripts/multicam_calibrator_gui.py
```

## Calibration Modes

- `eye_in_hand`: solves `link_tcp -> wrist_camera_color_optical_frame`
- `eye_to_hand_known_board`: solves `base_link -> mid_camera_color_optical_frame`
- `camera_to_camera`: solves `mid_camera_color_optical_frame -> far_camera_color_optical_frame`

`eye_to_hand_known_board` requires a measured `T_tool_board`.
