from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup


setup_args = generate_distutils_setup(
    packages=[
        "piper_multicam_calibrator",
        "piper_multicam_calibrator.boards",
        "piper_multicam_calibrator.core",
        "piper_multicam_calibrator.dataset",
        "piper_multicam_calibrator.gui",
        "piper_multicam_calibrator.report",
        "piper_multicam_calibrator.ros",
        "piper_multicam_calibrator.solvers",
    ],
    package_dir={"": "src"},
)

setup(**setup_args)
