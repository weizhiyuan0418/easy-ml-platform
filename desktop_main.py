from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


BASE_DIR = Path(__file__).resolve().parent


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str, *, timeout: float = 25.0) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status < 500:
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(0.4)
    raise RuntimeError(f"本地服务启动超时: {last_error}")


class DesktopShell(QMainWindow):
    def __init__(self, url: str, process: subprocess.Popen) -> None:
        super().__init__()
        self.url = url
        self.process = process
        self.setWindowTitle("通用机器学习软件")
        self.resize(420, 180)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        title = QLabel("通用机器学习软件已启动")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        info = QLabel(f"本地 Web 地址：{url}")
        info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        button = QPushButton("打开界面")
        button.clicked.connect(self.open_url)

        layout.addWidget(title)
        layout.addWidget(info)
        layout.addWidget(button)
        layout.addStretch(1)
        self.setCentralWidget(root)

    def open_url(self) -> None:
        QDesktopServices.openUrl(QUrl(self.url))

    def closeEvent(self, event) -> None:  # noqa: N802, ANN001
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        super().closeEvent(event)


def main() -> int:
    port = find_free_port()
    url = f"http://127.0.0.1:{port}/"
    process = subprocess.Popen(
        [
            sys.executable,
            "manage.py",
            "runserver",
            f"127.0.0.1:{port}",
            "--noreload",
        ],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server(url)
    except Exception:
        process.terminate()
        raise

    app = QApplication.instance() or QApplication(sys.argv)
    shell = DesktopShell(url, process)
    shell.show()
    shell.open_url()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
