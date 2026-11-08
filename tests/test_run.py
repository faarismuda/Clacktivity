from pathlib import Path
import sys

from run import create_uvicorn_config, ensure_std_streams, main, parse_args
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
