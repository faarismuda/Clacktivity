import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
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
    assert "Clacktivity" in index_res.text

    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "KeyboardHeatmap" in js_res.text


def test_horizontal_key_stream_markup_and_styles(tmp_path: Path):
    db = Database(tmp_path / "stream_ui.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "VS Code"))
    app = create_app(db=db, collector=collector)
    client = TestClient(app)

    index_res = client.get("/")
    assert index_res.status_code == 200
    html = index_res.text
    assert "Horizontal Key Stream" in html
    assert 'id="horizontal-events-stream"' in html
    assert 'id="stream-search"' in html
    assert 'id="btn-stream-prev"' in html
    assert 'id="btn-stream-next"' in html
    assert 'id="stream-page-info"' in html
    assert 'data-stream-order="asc"' in html
    assert 'data-stream-order="desc"' in html

    css_res = client.get("/static/css/styles.css")
    assert css_res.status_code == 200
    assert ".key-stream-box" in css_res.text
    assert ".stream-chip" in css_res.text
    assert "#stream-search" in css_res.text


def test_horizontal_key_stream_js_and_pagination(tmp_path: Path):
    db = Database(tmp_path / "stream_js.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "editor.py"))
    collector.handle_raw_event(RawKeyEvent(1731045600.1, 0x48, 0, True))  # H
    collector.handle_raw_event(RawKeyEvent(1731045600.2, 0x49, 0, True))  # I
    collector.flush()

    app = create_app(db=db, collector=collector)
    client = TestClient(app)

    viewer_res = client.get("/static/js/log_viewer.js")
    assert viewer_res.status_code == 200
    assert "export function renderHorizontalEventsStream" in viewer_res.text
    assert "export function insertLiveStreamChip" in viewer_res.text
    assert "buildStreamEventChipHtml" in viewer_res.text
    assert "${escapeHtml(ev.modifiers)}+${escapeHtml(ev.key_label)}" not in viewer_res.text

    app_js_res = client.get("/static/js/app.js")
    assert app_js_res.status_code == 200
    assert "renderHorizontalEventsStream" in app_js_res.text
    assert "insertLiveStreamChip" in app_js_res.text
    assert "loadStreamEvents" in app_js_res.text
    assert "streamLimit: 250" in app_js_res.text

    events_res = client.get("/api/events?date=2024-11-08&limit=250&offset=0")
    assert events_res.status_code == 200
    payload = events_res.json()
    assert payload["total"] == 2
    assert payload["limit"] == 250
    assert [item["key_label"] for item in payload["items"]] == ["I", "H"]


def test_dashboard_ux_improvements(tmp_path: Path):
    db = Database(tmp_path / "ux.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "editor.py"))
    app = create_app(db=db, collector=collector)
    client = TestClient(app)

    html = client.get("/").text
    assert 'rel="icon"' in html
    assert 'data-stream-mode="raw"' in html
    assert 'data-stream-mode="clean"' in html

    css = client.get("/static/css/styles.css").text
    assert ".btn:disabled" in css
    assert ".stream-line-break" in css
    assert ".data-tr[data-key-code]:hover" in css

    charts_js = client.get("/static/js/charts.js").text
    assert "onShortcutClick" in charts_js

    viewer_js = client.get("/static/js/log_viewer.js").text
    assert "stream-line-break" in viewer_js

    app_js = client.get("/static/js/app.js").text
    assert "renderLogPageInfo" in app_js
    assert "streamMode" in app_js
    assert "scheduleLiveAnalyticsRefresh" in app_js


def test_visual_ui_and_filter_reset_fixes(tmp_path: Path):
    db = Database(tmp_path / "visual_fixes.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "editor.py"))
    app = create_app(db=db, collector=collector)
    client = TestClient(app)

    css = client.get("/static/css/styles.css").text
    assert "color-scheme: dark" in css
    assert "white-space: nowrap" in css
    assert ".kb-numpad-grid .kb-legend" in css

    app_js = client.get("/static/js/app.js").text
    assert '$("key-table-search").value = ""' in app_js
    assert "of selected day" in app_js

    viewer_js = client.get("/static/js/log_viewer.js").text
    assert 'containerEl.scrollTop = order === "asc" ? containerEl.scrollHeight : 0' in viewer_js


def test_api_and_websocket_password_lock_flow(tmp_path: Path):
    db = Database(tmp_path / "auth_api.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "VS Code"))
    app = create_app(db=db, collector=collector)
    client = TestClient(app)

    # 1. Initially unlocked
    auth_status = client.get("/api/auth/status").json()
    assert auth_status == {
        "password_enabled": False,
        "authenticated": True,
        "token_expiration_hours": 2,
    }
    assert client.get("/api/status").status_code == 200

    # 2. Validation when enabling password
    missing_pwd_res = client.post("/api/auth/password", json={"token_expiration_hours": 4})
    assert missing_pwd_res.status_code == 400

    # Enable password via POST /api/auth/password
    set_res = client.post(
        "/api/auth/password",
        json={"new_password": "secret123", "token_expiration_hours": 4},
    )
    assert set_res.status_code == 200
    assert set_res.json()["password_enabled"] is True

    bad_exp_res = client.post(
        "/api/auth/password",
        json={"current_password": "secret123", "token_expiration_hours": "not-a-number"},
    )
    assert bad_exp_res.status_code == 400

    # Fresh unauthenticated client should be blocked from API and WebSocket
    anon_client = TestClient(app)
    anon_status = anon_client.get("/api/auth/status").json()
    assert anon_status == {
        "password_enabled": True,
        "authenticated": False,
        "token_expiration_hours": 4,
    }
    assert anon_client.get("/api/status").status_code == 401
    assert anon_client.post("/api/status/toggle").status_code == 401
    assert anon_client.get("/api/analytics/daily").status_code == 401
    assert anon_client.get("/api/events").status_code == 401
    assert anon_client.get("/api/export").status_code == 401

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with anon_client.websocket_connect("/ws/live") as ws:
            ws.receive_json()
    assert exc_info.value.code == 1008

    # 3. Wrong password returns 401, correct password logs in and sets cookie
    bad_login = anon_client.post("/api/auth/login", json={"password": "wrong"})
    assert bad_login.status_code == 401

    good_login = anon_client.post("/api/auth/login", json={"password": "secret123"})
    assert good_login.status_code == 200
    assert anon_client.get("/api/status").status_code == 200

    with anon_client.websocket_connect("/ws/live") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "status"

    # 4. Changing or disabling password requires current_password
    unauth_disable = anon_client.post(
        "/api/auth/password",
        json={"current_password": "wrong", "disable": True},
    )
    assert unauth_disable.status_code == 401

    # 5. Logout locks the session again
    anon_client.post("/api/auth/logout")
    assert anon_client.get("/api/status").status_code == 401

    # 6. Disable password lock using valid current_password
    disable_res = client.post(
        "/api/auth/password",
        json={"current_password": "secret123", "disable": True},
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["password_enabled"] is False
    assert anon_client.get("/api/status").status_code == 200


def test_password_lock_ui_markup_and_module(tmp_path: Path):
    db = Database(tmp_path / "ui_lock.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "VS Code"))
    app = create_app(db=db, collector=collector)
    client = TestClient(app)

    html = client.get("/").text
    assert 'id="btn-security"' in html
    assert 'id="btn-lock-now"' in html
    assert 'id="lock-overlay"' in html
    assert 'id="lock-form"' in html
    assert 'id="security-modal"' in html
    assert 'id="security-form"' in html

    auth_js = client.get("/static/js/auth.js")
    assert auth_js.status_code == 200
    assert "export async function initAuth" in auth_js.text
    assert "/api/auth/login" in auth_js.text
    assert "/api/auth/logout" in auth_js.text
    assert "/api/auth/password" in auth_js.text

    css = client.get("/static/css/styles.css").text
    assert ".lock-overlay" in css
    assert ".modal-backdrop" in css
    assert "--accent-rose:" in css





