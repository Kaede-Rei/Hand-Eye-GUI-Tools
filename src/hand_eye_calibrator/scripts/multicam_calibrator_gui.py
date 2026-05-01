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
    dirs = []
    for value in site.getsitepackages() + [site.getusersitepackages()]:
        if value:
            dirs.append(Path(value))
    for value in sys.path:
        if value:
            dirs.append(Path(value))
    return dirs


def _bootstrap_pyside6_qt() -> None:
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
        self.message = message
        self.enabled = sys.stderr.isatty()
        self.done = threading.Event()
        self.thread: threading.Thread | None = None

    def __enter__(self):
        if self.enabled:
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if not self.enabled:
            return
        self.done.set()
        if self.thread is not None:
            self.thread.join(timeout=0.4)
        sys.stderr.write("\r" + " " * (len(self.message) + 12) + "\r")
        sys.stderr.flush()

    def _run(self) -> None:
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
