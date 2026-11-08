from src.analytics import compute_daily_analytics, compute_wpm_metrics
from src.exporter import export_events


def test_compute_daily_analytics_and_wpm():
    base_ts = 1731045600.0
    events = []
    # Simulate 25 printable keystrokes over 10 seconds (5 words in 1/6 min = 30 WPM)
    for i in range(25):
        events.append({
            "id": i + 1,
            "timestamp": base_ts + (i * 0.4),
            "iso_time": f"2026-11-08 10:00:{int(i * 0.4):02d}.000",
            "date_str": "2026-11-08",
            "hour": 10,
            "vk_code": 0x41,
            "key_code": "KeyA" if i < 20 else "Space",
            "key_label": "A" if i < 20 else "Space",
            "modifiers": "Ctrl" if i == 0 else "",
            "combo_label": "Ctrl+A" if i == 0 else "",
            "is_printable": 1,
            "app_name": "Code.exe" if i < 15 else "chrome.exe",
            "window_title": "Editor",
        })

    wpm = compute_wpm_metrics(events)
    assert wpm["active_seconds"] > 9.0
    assert wpm["avg_wpm"] > 25.0
    assert wpm["peak_wpm"] > 0.0

    report = compute_daily_analytics(events, "2026-11-08")
    assert report["summary"]["total_keystrokes"] == 25
    assert report["summary"]["unique_keys"] == 2
    assert report["summary"]["top_key"]["key_code"] == "KeyA"
    assert report["summary"]["top_app"]["app_name"] == "Code.exe"
    assert report["key_counts"]["KeyA"] == 20
    assert report["hourly"][10] == 25
    assert report["top_shortcuts"][0]["combo"] == "Ctrl+A"
    assert len(report["apps"]) == 2
    assert len(report["all_keys"]) == 2


def test_exporter_csv_and_json():
    events = [{
        "id": 1,
        "timestamp": 1731045600.0,
        "iso_time": "2026-11-08 10:00:00.000",
        "date_str": "2026-11-08",
        "hour": 10,
        "vk_code": 65,
        "key_code": "KeyA",
        "key_label": "A",
        "modifiers": "",
        "combo_label": "",
        "is_printable": 1,
        "app_name": "Code.exe",
        "window_title": "Editor",
    }]
    csv_body, mime, fname = export_events(events, fmt="csv", mode="raw")
    assert "KeyA" in csv_body
    assert mime == "text/csv"
    assert fname.endswith(".csv")

    json_body, jmime, jfname = export_events(events, fmt="json", mode="summary")
    assert "KeyA" in json_body
    assert jmime == "application/json"
    assert jfname.endswith(".json")
