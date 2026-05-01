#!/usr/bin/env python3
from __future__ import annotations

import os
import site
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _candidate_site_dirs() -> list[Path]:
    """收集可能包含 PySide6 Qt 运行库的 site-packages 目录

    Args:
        None: 无输入参数

    Returns:
        list[Path]: 函数执行结果
    """
    dirs = []
    for value in site.getsitepackages() + [site.getusersitepackages()]:
        if value:
            dirs.append(Path(value))
    for value in sys.path:
        if value:
            dirs.append(Path(value))
    return dirs


def _bootstrap_pyside6_qt() -> None:
    """设置 PySide6 Qt 运行库路径并在需要时重启进程

    Args:
        None: 无输入参数

    Returns:
        None: 无返回值
    """
    if os.environ.get("MULTICAM_HAND_EYE_QT_BOOTSTRAPPED") == "1":
        return
    for base in _candidate_site_dirs():
        qt_lib = base / "PySide6" / "Qt" / "lib"
        qml_dir = base / "PySide6" / "Qt" / "qml"
        plugins_dir = base / "PySide6" / "Qt" / "plugins"
        if not (qt_lib / "libQt6Core.so.6").exists():
            continue
        env = os.environ.copy()
        env["MULTICAM_HAND_EYE_QT_BOOTSTRAPPED"] = "1"
        old_ld = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = str(qt_lib) + (os.pathsep + old_ld if old_ld else "")
        if qml_dir.exists():
            old_qml = env.get("QML2_IMPORT_PATH", "")
            env["QML2_IMPORT_PATH"] = str(qml_dir) + (
                os.pathsep + old_qml if old_qml else ""
            )
        if plugins_dir.exists():
            old_plugins = env.get("QT_PLUGIN_PATH", "")
            env["QT_PLUGIN_PATH"] = str(plugins_dir) + (
                os.pathsep + old_plugins if old_plugins else ""
            )
        os.execvpe(sys.executable, [sys.executable, *sys.argv], env)


_bootstrap_pyside6_qt()


class _TerminalSpinner:
    def __init__(self, message: str):
        """初始化对象并保存运行所需的状态

        Args:
            message (str): 参数 message

        Returns:
            None: 无返回值
        """
        self.message = message
        self.enabled = sys.stderr.isatty()
        self.done = threading.Event()
        self.thread: threading.Thread | None = None

    def __enter__(self):
        """进入上下文管理器并启动相关资源

        Args:
            None: 无输入参数

        Returns:
            None: 当前上下文管理器实例
        """
        if self.enabled:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        """退出上下文管理器并释放相关资源

        Args:
            exc_type (Any): 参数 exc_type
            exc (Any): 参数 exc
            tb (Any): 参数 tb

        Returns:
            None: 不抑制上下文异常
        """
        if not self.enabled:
            return
        self.done.set()
        if self.thread is not None:
            self.thread.join(timeout=0.4)
        sys.stderr.write("\r" + " " * (len(self.message) + 12) + "\r")
        sys.stderr.flush()

    def _run(self) -> None:
        """在后台循环执行轻量状态更新

        Args:
            None: 无输入参数

        Returns:
            None: 无返回值
        """
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        i = 0
        while not self.done.is_set():
            sys.stderr.write(f"\r{frames[i % len(frames)]} {self.message}")
            sys.stderr.flush()
            i += 1
            time.sleep(0.08)


with _TerminalSpinner("加载 Qt 与标定后端..."):
    from hand_eye_calibrator.gui.main_window import main

if __name__ == "__main__":
    main()
