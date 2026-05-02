from .base import BoardObservation


def create_board_detector(config: dict):
    """根据标定板配置创建对应的检测器实例

    Args:
        config (dict): 参数 config

    Returns:
        None: 无返回值
    """
    board_type = str(config.get("type", "chessboard")).lower()
    if board_type == "chessboard":
        from .chessboard import ChessboardDetector

        return ChessboardDetector(config)
    if board_type == "charuco":
        from .charuco import CharucoDetector

        return CharucoDetector(config)
    raise ValueError(f"unsupported board type: {board_type}")


__all__ = [
    "BoardObservation",
    "create_board_detector",
]
