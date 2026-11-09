from pathlib import Path
import sys

from run import create_uvicorn_config, ensure_std_streams, main, parse_args, spawn_background_worker
from src.config import get_app_dir, get_resource_dir, load_settings
from fastapi import FastAPI


def test_parse_args_supports_foreground():
    args = parse_args(["--foreground", "--port", "9000"])
    assert args.foreground is True
    assert args.port == 9000


def test_default_main_spawns_detached_background(monkeypatch):
    spawned = {}

    def fake_spawn(argv):
        spawned["argv"] = argv
        return 12345

    monkeypatch.setattr("run.is_port_in_use", lambda h, p: False)
    monkeypatch.setattr("run.spawn_background_worker", fake_spawn)
    monkeypatch.setattr("webbrowser.open", lambda url: None)

    rc = main(["--port", "18777", "--no-browser"])
    assert rc == 0
    assert "--foreground" in spawned["argv"]
    assert "18777" in spawned["argv"]


def test_windowless_pythonw_streams_and_uvicorn_config(tmp_path: Path, monkeypatch):
    """Ensure pythonw mode (where stdout and stderr are None) does not crash Uvicorn or print()."""
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    log_file = tmp_path / "app.log"
    ensure_std_streams(log_file)

    assert sys.stdout is not None
    assert sys.stderr is not None

    # Standard print() and uvicorn.Config must succeed when started under pythonw
    print("Testing windowless print output")
    app = FastAPI()
    cfg = create_uvicorn_config(app, host="127.0.0.1", port=18765)
    assert cfg.port == 18765


def test_frozen_mode_paths_and_settings(tmp_path: Path, monkeypatch):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    exe_path = dist_dir / "Clacktivity.exe"
    mei_dir = tmp_path / "_mei_bundle"
    mei_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_path))
    monkeypatch.setattr(sys, "_MEIPASS", str(mei_dir), raising=False)

    assert get_app_dir() == dist_dir.resolve()
    assert get_resource_dir() == mei_dir.resolve()
    assert load_settings().db_path == dist_dir.resolve() / "data" / "clacktivity.db"

    # Legacy database fallback when keyboard_analytics.db already exists
    legacy_db = dist_dir / "data" / "keyboard_analytics.db"
    legacy_db.parent.mkdir(parents=True, exist_ok=True)
    legacy_db.write_bytes(b"sqlite")
    assert load_settings().db_path == legacy_db.resolve()


def test_spawn_background_worker_frozen_omits_script_path(tmp_path: Path, monkeypatch):
    exe_path = tmp_path / "Clacktivity.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_path))

    captured = {}

    class DummyProc:
        pid = 4321

    def fake_popen(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return DummyProc()

    monkeypatch.setattr("subprocess.Popen", fake_popen)

    pid = spawn_background_worker(["--foreground", "--port", "8765"])
    assert pid == 4321
    assert captured["cmd"] == [str(exe_path), "--foreground", "--port", "8765"]
    assert captured["cwd"] == str(tmp_path.resolve())

