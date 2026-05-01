from .base import CalibrationResult
from .eye_in_hand_solver import EyeInHandSolver
from .eye_to_hand_solver import EyeToHandKnownBoardSolver
from .camera_to_camera_solver import CameraToCameraSolver


def create_solver(task_type: str, **kwargs):
    if task_type == "eye_in_hand":
        return EyeInHandSolver(**kwargs)
    if task_type in ("eye_to_hand", "eye_to_hand_known_board"):
        return EyeToHandKnownBoardSolver(**kwargs)
    if task_type == "camera_to_camera":
        return CameraToCameraSolver(**kwargs)
    raise ValueError(f"unsupported task type: {task_type}")


__all__ = ["CalibrationResult", "EyeInHandSolver", "EyeToHandKnownBoardSolver", "CameraToCameraSolver", "create_solver"]
