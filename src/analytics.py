"""Analytics calculation engine for daily keyboard metrics, WPM, and app breakdowns."""

from collections import Counter, defaultdict
from typing import Any

BURST_MAX_GAP_SEC = 5.0
MIN_BURST_DURATION_SEC = 2.0
CHARS_PER_WORD = 5.0


def compute_wpm_metrics(events: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate active typing duration, average active WPM, and peak 1-minute WPM."""
    printable_ts = [
        float(ev["timestamp"]) for ev in events if int(ev.get("is_printable", 0)) == 1
    ]
    if len(printable_ts) < 2:
        return {"active_seconds": 0.0, "avg_wpm": 0.0, "peak_wpm": 0.0}

    printable_ts.sort()
    total_active_sec = 0.0
    burst_chars = 0
    total_qualifying_chars = 0
    total_qualifying_sec = 0.0

    burst_start = printable_ts[0]
    prev_ts = printable_ts[0]
    burst_count = 1

    for ts in printable_ts[1:]:
        gap = ts - prev_ts
        if gap <= BURST_MAX_GAP_SEC:
            burst_count += 1
            prev_ts = ts
        else:
            duration = prev_ts - burst_start
            if duration > 0:
                total_active_sec += duration
            if duration >= MIN_BURST_DURATION_SEC:
                total_qualifying_sec += duration
                total_qualifying_chars += burst_count
            burst_start = ts
            prev_ts = ts
            burst_count = 1

    last_duration = prev_ts - burst_start
    if last_duration > 0:
        total_active_sec += last_duration
    if last_duration >= MIN_BURST_DURATION_SEC:
        total_qualifying_sec += last_duration
        total_qualifying_chars += burst_count

    avg_wpm = 0.0
    if total_qualifying_sec > 0:
        words = total_qualifying_chars / CHARS_PER_WORD
        avg_wpm = (words / total_qualifying_sec) * 60.0

    # Rolling window peak WPM (60-second window, or scaled burst if < 60s total span)
    left = 0
    max_in_60s = 0
    for right, r_ts in enumerate(printable_ts):
        while r_ts - printable_ts[left] > 60.0:
            left += 1
        window_count = right - left + 1
        if window_count > max_in_60s:
            max_in_60s = window_count

    total_span = max(printable_ts[-1] - printable_ts[0], 1.0)
    effective_window_sec = min(60.0, max(total_span, MIN_BURST_DURATION_SEC))
    peak_wpm = ((max_in_60s / CHARS_PER_WORD) / effective_window_sec) * 60.0

    return {
        "active_seconds": round(total_active_sec, 1),
        "avg_wpm": round(avg_wpm, 1),
        "peak_wpm": round(peak_wpm, 1),
    }


def compute_daily_analytics(events: list[dict[str, Any]], date_str: str) -> dict[str, Any]:
    """Compute comprehensive daily keyboard analytics for a given list of events."""
    total = len(events)
    hourly = [0] * 24
    key_counts: Counter[str] = Counter()
    key_labels: dict[str, str] = {}
    shortcut_counts: Counter[str] = Counter()
    modifier_counts: Counter[str] = Counter()
    app_counts: Counter[str] = Counter()
    app_keys: dict[str, Counter[str]] = defaultdict(Counter)

    for ev in events:
        hr = int(ev.get("hour", 0))
        if 0 <= hr < 24:
            hourly[hr] += 1

        kcode = str(ev.get("key_code", "Unknown"))
        klabel = str(ev.get("key_label", kcode))
        key_counts[kcode] += 1
        key_labels[kcode] = klabel

        combo = str(ev.get("combo_label", ""))
        if combo:
            shortcut_counts[combo] += 1

        mods = str(ev.get("modifiers", ""))
        if mods:
            modifier_counts[mods] += 1

        app = str(ev.get("app_name", "Unknown")) or "Unknown"
        app_counts[app] += 1
        app_keys[app][klabel] += 1

    wpm = compute_wpm_metrics(events)

    all_keys = [
        {
            "key_code": code,
            "key_label": key_labels.get(code, code),
            "count": cnt,
            "percentage": round((cnt / total) * 100.0, 2) if total else 0.0,
        }
        for code, cnt in key_counts.most_common()
    ]

    top_shortcuts = [
        {
            "combo": combo,
            "count": cnt,
            "percentage": round((cnt / total) * 100.0, 2) if total else 0.0,
        }
        for combo, cnt in shortcut_counts.most_common(15)
    ]

    apps = []
    for app_name, cnt in app_counts.most_common(20):
        top_app_keys = [
            {"key_label": kl, "count": kcnt}
            for kl, kcnt in app_keys[app_name].most_common(5)
        ]
        apps.append({
            "app_name": app_name,
            "count": cnt,
            "percentage": round((cnt / total) * 100.0, 2) if total else 0.0,
            "top_keys": top_app_keys,
        })

    top_key = all_keys[0] if all_keys else {"key_code": "-", "key_label": "-", "count": 0}
    top_app = apps[0] if apps else {"app_name": "-", "count": 0, "percentage": 0.0}
    peak_hour = max(range(24), key=lambda h: hourly[h]) if total else 0

    return {
        "date": date_str,
        "summary": {
            "total_keystrokes": total,
            "unique_keys": len(key_counts),
            "active_seconds": wpm["active_seconds"],
            "avg_wpm": wpm["avg_wpm"],
            "peak_wpm": wpm["peak_wpm"],
            "top_key": top_key,
            "top_app": top_app,
            "peak_hour": f"{peak_hour:02d}:00",
        },
        "key_counts": dict(key_counts),
        "all_keys": all_keys,
        "top_keys": all_keys[:15],
        "top_shortcuts": top_shortcuts,
        "hourly": hourly,
        "apps": apps,
    }
