# Details

Date : 2026-05-01 21:33:31

Directory /media/kaede-rei/AgroTech/home/ROS-Noetic-Workspace/hand-eye-ws/src

Total : 50 files,  2033 codes, 18 comments, 328 blanks, all 2379 lines

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [src/CMakeLists.txt](/src/CMakeLists.txt) | CMake | 58 | 0 | 10 | 68 |
| [src/hand\_eye\_calibrator/CMakeLists.txt](/src/hand_eye_calibrator/CMakeLists.txt) | CMake | 23 | 0 | 7 | 30 |
| [src/hand\_eye\_calibrator/README.md](/src/hand_eye_calibrator/README.md) | Markdown | 23 | 0 | 11 | 34 |
| [src/hand\_eye\_calibrator/config/board\_charuco.yaml](/src/hand_eye_calibrator/config/board_charuco.yaml) | YAML | 6 | 0 | 1 | 7 |
| [src/hand\_eye\_calibrator/config/board\_chessboard.yaml](/src/hand_eye_calibrator/config/board_chessboard.yaml) | YAML | 4 | 0 | 1 | 5 |
| [src/hand\_eye\_calibrator/config/c1\_three\_camera.yaml](/src/hand_eye_calibrator/config/c1_three_camera.yaml) | YAML | 48 | 0 | 5 | 53 |
| [src/hand\_eye\_calibrator/config/default.yaml](/src/hand_eye_calibrator/config/default.yaml) | YAML | 48 | 0 | 5 | 53 |
| [src/hand\_eye\_calibrator/package.xml](/src/hand_eye_calibrator/package.xml) | XML | 14 | 0 | 5 | 19 |
| [src/hand\_eye\_calibrator/scripts/collect\_dataset\_node.py](/src/hand_eye_calibrator/scripts/collect_dataset_node.py) | Python | 1 | 2 | 2 | 5 |
| [src/hand\_eye\_calibrator/scripts/export\_static\_tf.py](/src/hand_eye_calibrator/scripts/export_static_tf.py) | Python | 37 | 1 | 8 | 46 |
| [src/hand\_eye\_calibrator/scripts/multicam\_calibrator\_gui.py](/src/hand_eye_calibrator/scripts/multicam_calibrator_gui.py) | Python | 74 | 1 | 17 | 92 |
| [src/hand\_eye\_calibrator/scripts/run\_calibration.py](/src/hand_eye_calibrator/scripts/run_calibration.py) | Python | 56 | 1 | 11 | 68 |
| [src/hand\_eye\_calibrator/scripts/validate\_tf.py](/src/hand_eye_calibrator/scripts/validate_tf.py) | Python | 19 | 1 | 8 | 28 |
| [src/hand\_eye\_calibrator/setup.py](/src/hand_eye_calibrator/setup.py) | Python | 19 | 0 | 3 | 22 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/__init__.py) | Python | 1 | 1 | 2 | 4 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/boards/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/boards/__init__.py) | Python | 11 | 0 | 5 | 16 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/boards/base.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/boards/base.py) | Python | 30 | 0 | 6 | 36 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/boards/charuco.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/boards/charuco.py) | Python | 125 | 0 | 7 | 132 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/boards/chessboard.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/boards/chessboard.py) | Python | 91 | 0 | 7 | 98 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/core/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/core/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/core/io.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/core/io.py) | Python | 22 | 0 | 10 | 32 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/core/reprojection.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/core/reprojection.py) | Python | 8 | 0 | 4 | 12 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/core/rotation\_average.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/core/rotation_average.py) | Python | 2 | 0 | 2 | 4 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/core/transform.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/core/transform.py) | Python | 159 | 0 | 25 | 184 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/dataset/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/dataset/__init__.py) | Python | 3 | 0 | 2 | 5 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/dataset/loader.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/dataset/loader.py) | Python | 75 | 0 | 11 | 86 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/dataset/schema.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/dataset/schema.py) | Python | 43 | 0 | 13 | 56 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/dataset/writer.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/dataset/writer.py) | Python | 67 | 0 | 8 | 75 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/board\_panel.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/board_panel.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/calibration\_panel.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/calibration_panel.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/camera\_panel.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/camera_panel.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/main\_window.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/main_window.py) | Python | 448 | 0 | 46 | 494 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/sample\_panel.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/sample_panel.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/task\_panel.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/task_panel.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/gui/tf\_panel.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/gui/tf_panel.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/report/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/report/__init__.py) | Python | 2 | 0 | 2 | 4 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/report/exporter.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/report/exporter.py) | Python | 63 | 0 | 12 | 75 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/report/metrics.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/report/metrics.py) | Python | 2 | 0 | 2 | 4 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/report/plots.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/report/plots.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/ros/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/ros/__init__.py) | Python | 0 | 1 | 1 | 2 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/ros/camera\_cache.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/ros/camera_cache.py) | Python | 15 | 0 | 4 | 19 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/ros/tf\_reader.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/ros/tf_reader.py) | Python | 33 | 0 | 6 | 39 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/ros/topic\_reader.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/ros/topic_reader.py) | Python | 72 | 0 | 10 | 82 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/solvers/\_\_init\_\_.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/solvers/__init__.py) | Python | 13 | 0 | 5 | 18 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/solvers/base.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/solvers/base.py) | Python | 27 | 0 | 7 | 34 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/solvers/camera\_to\_camera\_solver.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/solvers/camera_to_camera_solver.py) | Python | 65 | 0 | 6 | 71 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/solvers/eye\_in\_hand\_solver.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/solvers/eye_in_hand_solver.py) | Python | 81 | 0 | 8 | 89 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/solvers/eye\_to\_hand\_solver.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/solvers/eye_to_hand_solver.py) | Python | 140 | 0 | 11 | 151 |
| [src/hand\_eye\_calibrator/src/hand\_eye\_calibrator/solvers/nonlinear\_refiner.py](/src/hand_eye_calibrator/src/hand_eye_calibrator/solvers/nonlinear_refiner.py) | Python | 5 | 1 | 3 | 9 |

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)