from __future__ import annotations

import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget


APP_NAME = "Easy ML Platform"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
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
    raise RuntimeError(f"Local service startup timed out: {last_error}")


def show_error(title: str, message: str) -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    QMessageBox.critical(None, title, message)
    _ = app


def run_migrations() -> None:
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    import django
    from django.core.management import call_command

    stdout = StringIO()
    stderr = StringIO()
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            django.setup()
            call_command("migrate", interactive=False, verbosity=1)
    except Exception as exc:  # noqa: BLE001
        details = stdout.getvalue() + "\n" + stderr.getvalue()
        raise RuntimeError(f"Database initialization failed: {exc}\n\n{details.strip()}") from exc


def run_django_server(host_port: str) -> None:
    import os

    run_migrations()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(["manage.py", "runserver", host_port, "--noreload"])


def read_log_tail(path: Path, *, max_chars: int = 4000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-max_chars:]


class DesktopShell(QMainWindow):
    def __init__(self, url: str, process: subprocess.Popen) -> None:
        super().__init__()
        self.url = url
        self.process = process
        self.setWindowTitle(APP_NAME)
        self.resize(420, 180)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(12)

        title = QLabel(f"{APP_NAME} is running")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 18px; font-weight: 700;")
        info = QLabel(f"Local Web URL: {url}")
        info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        button = QPushButton("Open UI")
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
    if len(sys.argv) >= 3 and sys.argv[1] == "--serve-django":
        run_django_server(sys.argv[2])
        return 0

    try:
        run_migrations()
    except Exception as exc:  # noqa: BLE001
        show_error("Startup failed", str(exc))
        return 1

    port = find_free_port()
    url = f"http://127.0.0.1:{port}/"
    log_dir = Path(tempfile.gettempdir()) / "easy_ml_platform"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / "django_stdout.log"
    stderr_path = log_dir / "django_stderr.log"
    stdout_fp = stdout_path.open("w", encoding="utf-8")
    stderr_fp = stderr_path.open("w", encoding="utf-8")
    server_command = [sys.executable, "--serve-django", f"127.0.0.1:{port}"]
    if not getattr(sys, "frozen", False):
        server_command = [sys.executable, str(Path(__file__).resolve()), "--serve-django", f"127.0.0.1:{port}"]
    process = subprocess.Popen(
        server_command,
        cwd=str(BASE_DIR),
        stdout=stdout_fp,
        stderr=stderr_fp,
    )
    try:
        wait_for_server(url)
    except Exception as exc:  # noqa: BLE001
        process.terminate()
        stdout_fp.close()
        stderr_fp.close()
        details = read_log_tail(stderr_path) or read_log_tail(stdout_path)
        show_error("Startup failed", f"{exc}\n\nLog path:\n{stderr_path}\n\n{details}")
        return 1

    app = QApplication.instance() or QApplication(sys.argv)
    shell = DesktopShell(url, process)
    shell.show()
    shell.open_url()
    try:
        return int(app.exec())
    finally:
        stdout_fp.close()
        stderr_fp.close()


if __name__ == "__main__":
    raise SystemExit(main())
