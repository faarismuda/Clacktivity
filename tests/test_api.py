from pathlib import Path
from fastapi.testclient import TestClient
from src.database import Database
from src.collector import EventCollector
from src.hook import RawKeyEvent
from src.api import create_app
from src.tray import create_tray_icon_image


def test_tray_icon_image_generation():
    img_live = create_tray_icon_image(is_paused=False)
    assert img_live.size == (64, 64)
    img_paused = create_tray_icon_image(is_paused=True)
    assert img_paused.size == (64, 64)


def test_api_endpoints(tmp_path: Path):
    db = Database(tmp_path / "api.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "VS Code"))
    collector.handle_raw_event(RawKeyEvent(1731045600.5, 0x41, 0, True))
    collector.flush()

    app = create_app(db=db, collector=collector)
    client = TestClient(app)

    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["is_paused"] is False

    toggle_res = client.post("/api/status/toggle")
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_paused"] is True

    dates = status_res.json()["available_dates"]
    assert "2024-11-08" in dates
    day = "2024-11-08"

    daily_res = client.get(f"/api/analytics/daily?date={day}")
    assert daily_res.status_code == 200
    data = daily_res.json()
    assert data["summary"]["total_keystrokes"] == 1
    assert data["key_counts"]["KeyA"] == 1

    events_res = client.get(f"/api/events?date={day}&limit=20&offset=0")
    assert events_res.status_code == 200
    assert events_res.json()["total"] == 1

    export_res = client.get(f"/api/export?start_date={day}&end_date={day}&format=csv&mode=raw")
    assert export_res.status_code == 200
    assert "KeyA" in export_res.text

    index_res = client.get("/")
    assert index_res.status_code == 200
    assert "Keyboard Analytics" in index_res.text

    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "KeyboardHeatmap" in js_res.text
