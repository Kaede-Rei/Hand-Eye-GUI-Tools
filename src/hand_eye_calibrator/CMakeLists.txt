cmake_minimum_required(VERSION 3.0.2)
project(hand_eye_calibrator)

find_package(catkin REQUIRED COMPONENTS
  rospy
  sensor_msgs
  tf2_ros
)

catkin_python_setup()

catkin_package()

catkin_install_python(PROGRAMS
  scripts/multicam_calibrator_gui.py
  scripts/collect_dataset_node.py
  scripts/run_calibration.py
  scripts/validate_tf.py
  scripts/export_static_tf.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY config datasets
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(DIRECTORY src/hand_eye_calibrator/gui/qml
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/gui
)
