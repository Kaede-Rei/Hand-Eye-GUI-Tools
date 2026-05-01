# 多功能手眼标定工具 ROS 包

This ROS Noetic package provides the multi-function hand-eye calibration GUI and
solver backend.

## GUI

The GUI is implemented with Qt. The Python backend exposes ROS, dataset and
solver operations to the desktop interface.

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

- `eye_in_hand`: solves end-effector link -> end-effector camera
- `eye_to_hand` / `eye_to_hand_known_board`: solves base/world link -> fixed camera
- `camera_to_camera`: solves reference camera -> target camera

`eye_to_hand_known_board` requires a measured `T_tool_board`.
