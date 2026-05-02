#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/devel/setup.bash"
rosrun hand_eye_calibrator multicam_calibrator_gui.py
