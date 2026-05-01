from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup

setup_args = generate_distutils_setup(
    packages=[
        "hand_eye_calibrator",
        "hand_eye_calibrator.boards",
        "hand_eye_calibrator.core",
        "hand_eye_calibrator.dataset",
        "hand_eye_calibrator.gui",
        "hand_eye_calibrator.report",
        "hand_eye_calibrator.ros",
        "hand_eye_calibrator.solvers",
    ],
    package_dir={"": "src"},
    package_data={
        "hand_eye_calibrator": ["gui/qml/*.qml"],
    },
)

setup(**setup_args)
