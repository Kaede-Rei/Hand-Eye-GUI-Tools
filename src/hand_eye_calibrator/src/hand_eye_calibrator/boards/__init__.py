from .base import BoardObservation
from .chessboard import ChessboardDetector
from .charuco import CharucoDetector


def create_board_detector(config: dict):
    board_type = str(config.get("type", "chessboard")).lower()
    if board_type == "chessboard":
        return ChessboardDetector(config)
    if board_type == "charuco":
        return CharucoDetector(config)
    raise ValueError(f"unsupported board type: {board_type}")


__all__ = ["BoardObservation", "ChessboardDetector", "CharucoDetector", "create_board_detector"]
