# Windows Keyboard Analytics

A lightweight Windows keyboard analytics application that runs quietly in the System Tray, records every key press event (with millisecond timestamps, active modifiers, and foreground application/window context), and serves a real-time interactive Web Dashboard on `http://127.0.0.1:8765`.

## Features

- **Low-Level Win32 Keyboard Capture (`WH_KEYBOARD_LL`)**: Records every key press event (including key hold auto-repeats) with zero typing lag using an asynchronous queue and SQLite WAL micro-batching.
- **Interactive Visual Keyboard Heatmap**: Supports **100% Full-size**, **80% TKL**, **75%**, and **60%** US ANSI keyboard layouts with heat-map color scaling, per-key counts, click-to-filter, and live WebSocket key-flash animation.
- **Daily & Hourly Analytics**: View total keystrokes, unique keys, top keys, top modifier shortcuts (`Ctrl+C`, `Ctrl+V`, `Alt+Tab`), and 24-hour activity charts (`00:00`–`23:00`).
- **Typing Speed (WPM)**: Tracks Average Active WPM, Peak 1-Minute WPM, and total active typing duration per day.
- **Per-Application Breakdown**: Ranks applications (`Code.exe`, `chrome.exe`, etc.) by keystroke volume and shows top keys pressed per app.
- **Daily Key Table & Raw Event Log**: Filter by any date to inspect the complete list of keys pressed that day as well as the sequential raw event log.
- **System Tray & Export**: Pause/Resume recording or open the dashboard from the Windows System Tray, and export daily or range data to **CSV** or **JSON**.

## Quick Start

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application (automatically detaches to background & opens dashboard)
python run.py
```

The dashboard will open automatically at `http://127.0.0.1:8765`, and an icon will appear in your Windows System Tray.

## Running Tests

```powershell
pytest -v
```
