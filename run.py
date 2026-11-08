"""Application entrypoint for Windows Keyboard Analytics."""

import argparse
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from typing import Any
import webbrowser

import uvicorn

from src.api import create_app
from src.collector import EventCollector
from src.config import load_settings
from src.database import Database
from src.hook import Win32KeyboardHook
from src.tray import SystemTrayApp

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000


def ensure_std_streams(log_path: Path | None = None) -> None:
    """Redirect stdout and stderr to a log file when running under windowless pythonw.exe."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    if log_path is None:
        log_path = Path(__file__).resolve().parent / "data" / "app.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stream = open(log_path, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream


def create_uvicorn_config(app: Any, host: str, port: int) -> uvicorn.Config:
    """Create a Uvicorn Config safe for both console python.exe and windowless pythonw.exe."""
    return uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="warning",
        log_config=None,
    )


def is_port_in_use(host: str, port: int) -> bool:
    """Return True if a local server is already listening on (host, port)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def spawn_background_worker(child_args: list[str]) -> int:
    """Spawn a detached background process that survives when the parent CMD window is closed."""
    base_dir = Path(__file__).resolve().parent
    log_path = base_dir / "data" / "app.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "a", encoding="utf-8", buffering=1)

    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), *child_args],
        cwd=str(base_dir),
        creationflags=flags,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=log_file,
        close_fds=True,
    )
    return int(proc.pid)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for host, port, and runtime mode."""
    parser = argparse.ArgumentParser(description="Windows Keyboard Analytics")
    parser.add_argument("--host", type=str, default=None, help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (default: 8765)")
    parser.add_argument("--foreground", action="store_true", help="Keep process attached to current terminal")
    parser.add_argument("--no-tray", action="store_true", help="Run without Windows System Tray icon")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically on start")
    parser.add_argument("--no-hook", action="store_true", help="Disable low-level Win32 keyboard hook")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Initialize components and run the Keyboard Analytics service."""
    ensure_std_streams()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    args = parse_args(raw_argv)
    settings = load_settings()

    host = args.host or settings.host
    port = args.port or settings.port
    dashboard_url = f"http://{host}:{port}"

    if is_port_in_use(host, port):
        print(f"Keyboard Analytics is already running in the background at {dashboard_url}")
        if not args.no_browser:
            webbrowser.open(dashboard_url)
        return 0

    if not args.foreground and not args.no_tray:
        pid = spawn_background_worker(["--foreground", *raw_argv])
        for _ in range(15):
            if is_port_in_use(host, port):
                break
            time.sleep(0.15)
        print(f"Keyboard Analytics started in background (PID {pid}) at {dashboard_url}")
        print("You can safely close this terminal window. Use the System Tray icon to Quit.")
        return 0

    db = Database(settings.db_path)
    db.init_db()

    collector = EventCollector(
        db=db,
        batch_interval_sec=settings.batch_interval_sec,
        batch_max_size=settings.batch_max_size,
    )
    collector.start_worker()

    hook: Win32KeyboardHook | None = None
    if not args.no_hook:
        hook = Win32KeyboardHook(on_event=collector.enqueue)
        hook.start()

    app = create_app(db=db, collector=collector)
    uv_config = create_uvicorn_config(app=app, host=host, port=port)
    server = uvicorn.Server(uv_config)

    shutdown_once = threading.Event()

    def shutdown_all() -> None:
        if shutdown_once.is_set():
            return
        shutdown_once.set()
        if hook is not None:
            hook.stop()
        collector.stop_worker()
        server.should_exit = True

    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(dashboard_url)).start()

    print(f"Keyboard Analytics running at {dashboard_url}")
    print("Press Ctrl+C or use the System Tray icon to quit.")

    if args.no_tray:
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, lambda *_: shutdown_all())
            signal.signal(signal.SIGTERM, lambda *_: shutdown_all())
        try:
            server.run()
        finally:
            shutdown_all()
        return 0

    server_thread = threading.Thread(target=server.run, name="UvicornServer", daemon=True)
    server_thread.start()

    tray = SystemTrayApp(
        collector=collector,
        dashboard_url=dashboard_url,
        on_quit=shutdown_all,
    )
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, lambda *_: (tray.stop(), shutdown_all()))
    try:
        tray.run()
    finally:
        shutdown_all()
        time.sleep(0.2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
