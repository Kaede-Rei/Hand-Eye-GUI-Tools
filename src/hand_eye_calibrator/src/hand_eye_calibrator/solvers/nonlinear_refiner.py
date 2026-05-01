"""Placeholder for future joint robot-world/hand-eye nonlinear refinement."""


def refine_eye_to_hand_unknown_board(*args, **kwargs):
    """保留接口，用于未来实现非线性联合优化

    Args:
        *args (Any): 参数 *args
        **kwargs (Any): 参数 **kwargs

    Returns:
        None: 无返回值
    """
    raise NotImplementedError(
        "Unknown T_tool_board robot-world/hand-eye nonlinear refinement is not implemented yet. "
        "Use eye_to_hand_known_board with a measured T_tool_board for the current GUI."
    )
