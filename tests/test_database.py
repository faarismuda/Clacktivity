from pathlib import Path
from src.database import Database


def test_insert_and_query_events(tmp_path: Path):
    db = Database(tmp_path / "test_keys.db")
    db.init_db()

    sample_events = [
        {
            "timestamp": 1731045600.125,
            "iso_time": "2026-11-08 12:00:00.125",
            "date_str": "2026-11-08",
            "hour": 12,
            "vk_code": 0x41,
            "key_code": "KeyA",
            "key_label": "A",
            "modifiers": "",
            "combo_label": "",
            "is_printable": 1,
            "app_name": "Code.exe",
            "window_title": "main.py - VS Code",
        },
        {
            "timestamp": 1731045601.500,
            "iso_time": "2026-11-08 12:00:01.500",
            "date_str": "2026-11-08",
            "hour": 12,
            "vk_code": 0x43,
            "key_code": "KeyC",
            "key_label": "C",
            "modifiers": "Ctrl",
            "combo_label": "Ctrl+C",
            "is_printable": 1,
            "app_name": "chrome.exe",
            "window_title": "Docs - Google Chrome",
        },
    ]

    inserted = db.insert_events_batch(sample_events)
    assert inserted == 2
    assert db.get_available_dates() == ["2026-11-08"]

    day_events = db.get_events_for_date("2026-11-08")
    assert len(day_events) == 2
    assert day_events[0]["key_code"] == "KeyA"
    assert day_events[1]["combo_label"] == "Ctrl+C"

    paged = db.get_paginated_events("2026-11-08", limit=10, offset=0, key_filter="KeyC")
    assert paged["total"] == 1
    assert paged["items"][0]["combo_label"] == "Ctrl+C"

    range_events = db.get_events_in_range("2026-11-01", "2026-11-10")
    assert len(range_events) == 2


def test_paginated_events_filters_by_combo_label(tmp_path: Path):
    db = Database(tmp_path / "combo_filter.db")
    db.init_db()
    db.insert_events_batch([
        {
            "timestamp": 1731045600.0,
            "iso_time": "2026-11-08 10:00:00.000",
            "date_str": "2026-11-08",
            "hour": 10,
            "vk_code": 0x43,
            "key_code": "KeyC",
            "key_label": "C",
            "modifiers": "Ctrl",
            "combo_label": "Ctrl+C",
            "is_printable": 1,
            "app_name": "Code.exe",
            "window_title": "Editor",
        }
    ])
    res = db.get_paginated_events("2026-11-08", key_filter="Ctrl+C")
    assert res["total"] == 1
    assert res["items"][0]["combo_label"] == "Ctrl+C"


def test_paginated_events_search_matches_modifiers_column(tmp_path: Path):
    db = Database(tmp_path / "mod_search.db")
    db.init_db()
    db.insert_events_batch([
        {
            "timestamp": 1731045600.0,
            "iso_time": "2026-11-08 10:00:00.000",
            "date_str": "2026-11-08",
            "hour": 10,
            "vk_code": 0xA2,
            "key_code": "LeftControl",
            "key_label": "LCtrl",
            "modifiers": "Shift+Win",
            "combo_label": "",
            "is_printable": 0,
            "app_name": "Code.exe",
            "window_title": "Editor",
        }
    ])
    res = db.get_paginated_events("2026-11-08", search_query="Shift+Win")
    assert res["total"] == 1


