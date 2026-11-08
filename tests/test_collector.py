from pathlib import Path
from src.database import Database
from src.hook import RawKeyEvent
from src.collector import EventCollector
from src.window_tracker import get_active_window_info


def test_collector_processes_modifiers_and_pause(tmp_path: Path):
    db = Database(tmp_path / "collector.db")
    db.init_db()

    live_events = []
    collector = EventCollector(
        db=db,
        window_provider=lambda: ("Code.exe", "project - VS Code"),
    )
    unsubscribe = collector.subscribe(lambda ev: live_events.append(ev))

    # Press Left Ctrl down
    ev1 = collector.handle_raw_event(RawKeyEvent(1731045600.1, 0xA2, 0, True))
    assert ev1 is not None
    assert ev1["key_code"] == "LeftControl"

    # Press 'C' while Ctrl is held
    ev2 = collector.handle_raw_event(RawKeyEvent(1731045600.2, 0x43, 0, True))
    assert ev2 is not None
    assert ev2["modifiers"] == "Ctrl"
    assert ev2["combo_label"] == "Ctrl+C"
    assert ev2["app_name"] == "Code.exe"
    assert ev2["window_title"] == "project - VS Code"

    # Release Left Ctrl
    collector.handle_raw_event(RawKeyEvent(1731045600.3, 0xA2, 0, False))

    # Pause collector: keydowns should be ignored
    collector.set_paused(True)
    assert collector.is_paused is True
    ev3 = collector.handle_raw_event(RawKeyEvent(1731045600.4, 0x41, 0, True))
    assert ev3 is None

    # Toggle back to resume
    collector.toggle_paused()
    assert collector.is_paused is False

    flushed = collector.flush()
    assert flushed == 2
    key_live_events = [e for e in live_events if e["type"] == "key_event"]
    assert len(key_live_events) == 2
    assert len(live_events) == 4

    unsubscribe()


def test_window_tracker_returns_tuple():
    app_name, title = get_active_window_info()
    assert isinstance(app_name, str)
    assert len(app_name) > 0
    assert isinstance(title, str)


def test_collector_overlapping_same_group_modifiers_and_paused_modifiers(tmp_path: Path):
    db = Database(tmp_path / "collector_mods.db")
    db.init_db()
    collector = EventCollector(db=db, window_provider=lambda: ("Code.exe", "VS Code"))

    # Hold LeftShift (0xA0), tap and release RightShift (0xA1), then press 'A' (0x41)
    collector.handle_raw_event(RawKeyEvent(1731045600.1, 0xA0, 0, True))
    collector.handle_raw_event(RawKeyEvent(1731045600.2, 0xA1, 0, True))
    collector.handle_raw_event(RawKeyEvent(1731045600.3, 0xA1, 0, False))
    ev_a = collector.handle_raw_event(RawKeyEvent(1731045600.4, 0x41, 0, True))
    assert ev_a is not None
    assert ev_a["modifiers"] == "Shift"
    assert ev_a["combo_label"] == "Shift+A"

    # Release LeftShift
    collector.handle_raw_event(RawKeyEvent(1731045600.5, 0xA0, 0, False))

    # Pause recording, press LeftControl while paused, resume, then press 'C'
    collector.set_paused(True)
    collector.handle_raw_event(RawKeyEvent(1731045600.6, 0xA2, 0, True))
    collector.set_paused(False)
    ev_c = collector.handle_raw_event(RawKeyEvent(1731045600.7, 0x43, 0, True))
    assert ev_c is not None
    assert ev_c["modifiers"] == ""
    assert ev_c["combo_label"] == ""

