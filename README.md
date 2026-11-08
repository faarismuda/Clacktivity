# Windows Keyboard Analytics

A lightweight Windows keyboard analytics application that runs quietly in the System Tray, records every key press event (with millisecond timestamps, active modifiers, and foreground application/window context), and serves a real-time interactive Web Dashboard on `http://127.0.0.1:8765`.

## Features

- **Low-Level Win32 Keyboard Capture (`WH_KEYBOARD_LL`)**: Records every key press event (including key hold auto-repeats) with zero typing lag using an asynchronous queue and SQLite WAL micro-batching.
- **Interactive Visual Keyboard Heatmap**: Supports **100% Full-size**, **80% TKL**, **75%**, and **60%** US ANSI keyboard layouts with heat-map color scaling, per-key press counts, click-to-filter, and live WebSocket key-flash animation.
- **Daily & Hourly Analytics**: Tracks total keystrokes, unique keys, top keys, clickable top modifier shortcuts (`Ctrl+C`, `Ctrl+V`, `Alt+Tab`), and 24-hour activity distribution (`00:00`–`23:00`).
- **Typing Speed (WPM)**: Calculates Average Active WPM, Peak WPM (across active bursts and rolling 60-second windows), and total active typing duration per day.
- **Per-Application Breakdown**: Ranks foreground applications (`Code.exe`, `chrome.exe`, etc.) by keystroke volume and displays the top 5 keys pressed inside each app.
- **Daily Key Table & Raw Event Log**: Inspect complete key counts for any recorded date and browse the paginated, searchable millisecond-precision raw event log (`100` events/page) with live WebSocket row prepending.
- **Horizontal Key Stream**: View keystrokes as a horizontal sequence (`250` events/page) with:
  - **Display Modes**: Toggle between `1:1 Raw` (every raw event) and `Readable` (hides standalone modifier holds and inserts line breaks on `Enter`).
  - **Sort Order**: Switch between `Old → New` (chronological flow with auto-scroll to newest) and `New → Old`.
  - **Independent Search & Tooltips**: Filter by key, shortcut combo, app, or window title, and hover any keycap chip for full timestamp and window metadata.
- **Cross-Panel Filtering**: Click any keycap on the heatmap, top keys list, top modifier shortcuts list, all-keys table, or application breakdown to filter both the Raw Event Log and Horizontal Key Stream simultaneously.
- **System Tray & Data Export**: Pause/Resume recording or open the dashboard from the Windows System Tray, and export daily or date-range data as **Raw CSV**, **Daily Summary CSV**, or **JSON**.

## Quick Start

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the application (detaches to background, adds System Tray icon, and opens dashboard)
python run.py
```

The dashboard opens automatically at `http://127.0.0.1:8765`. If the service is already running in the background, running `python run.py` again simply opens the dashboard in your browser. You can also launch it without a console window using `pythonw run.py` (logs are written to `data/app.log`).

### CLI Options

```powershell
python run.py [options]
```

| Flag | Description |
| :--- | :--- |
| `--host HOST` | Bind address for the web server (default: `127.0.0.1`) |
| `--port PORT` | Bind port for the web server (default: `8765`) |
| `--foreground` | Keep the process attached to the current terminal instead of spawning a detached background worker |
| `--no-tray` | Run without the Windows System Tray icon |
| `--no-browser` | Do not open the web browser automatically on startup |
| `--no-hook` | Disable the low-level Win32 keyboard hook (useful for testing the web dashboard standalone) |

## Project Structure

- `run.py` — Application entrypoint, background process spawner, and CLI argument parser
- `src/hook.py` — Dedicated Win32 `WH_KEYBOARD_LL` message-pump thread
- `src/keymap.py` — Virtual-Key (`VK_*`) and extended scan-flag normalization
- `src/window_tracker.py` — Foreground window title and executable name resolver
- `src/collector.py` — Modifier state tracker, async queue consumer, SQLite batch writer, and live event broadcaster
- `src/database.py` — Thread-safe SQLite WAL storage and paginated query engine
- `src/analytics.py` — Daily summary, WPM burst/rolling calculation, and per-app aggregation
- `src/exporter.py` — Raw and daily summary CSV/JSON serializer
- `src/api.py` — FastAPI REST endpoints (`/api/status`, `/api/analytics/daily`, `/api/events`, `/api/export`) and `/ws/live` WebSocket
- `src/tray.py` — Windows System Tray icon and menu (`pystray` + `Pillow`)
- `static/` — Vanilla HTML5, CSS, and ES Module JavaScript frontend (`app.js`, `heatmap.js`, `layouts.js`, `charts.js`, `log_viewer.js`)

## Running Tests

```powershell
pytest -v
```
