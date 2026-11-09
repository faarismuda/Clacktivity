"""CSV and JSON data exporter for raw key events and daily summaries."""

from collections import Counter
import csv
import io
import json
from typing import Any


RAW_CSV_COLUMNS = [
    "id",
    "iso_time",
    "date_str",
    "hour",
    "key_code",
    "key_label",
    "modifiers",
    "combo_label",
    "app_name",
    "window_title",
]


def _build_summary_rows(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for ev in events:
        key = (
            str(ev.get("date_str", "")),
            str(ev.get("key_code", "")),
            str(ev.get("key_label", "")),
        )
        counts[key] += 1

    rows = [
        {
            "date_str": date_str,
            "key_code": key_code,
            "key_label": key_label,
            "count": count,
        }
        for (date_str, key_code, key_label), count in counts.most_common()
    ]
    rows.sort(key=lambda r: (r["date_str"], -r["count"]))
    return rows


def export_events(
    events: list[dict[str, Any]],
    fmt: str = "csv",
    mode: str = "raw",
    label: str = "export",
) -> tuple[str, str, str]:
    """Serialize events into CSV or JSON string and return (content, media_type, filename)."""
    fmt_clean = fmt.lower().strip()
    mode_clean = mode.lower().strip()

    rows = _build_summary_rows(events) if mode_clean == "summary" else events

    if fmt_clean == "json":
        payload = json.dumps(rows, indent=2, ensure_ascii=False)
        filename = f"clacktivity_{mode_clean}_{label}.json"
        return payload, "application/json", filename

    buf = io.StringIO()
    if mode_clean == "summary":
        fieldnames = ["date_str", "key_code", "key_label", "count"]
    else:
        fieldnames = RAW_CSV_COLUMNS

    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    filename = f"clacktivity_{mode_clean}_{label}.csv"
    return buf.getvalue(), "text/csv", filename
