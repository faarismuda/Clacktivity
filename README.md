# Clacktivity

A local-first keyboard activity and analytics tracker for Windows. Clacktivity runs quietly in the System Tray, records your keystrokes and active window context, and serves a live web dashboard at `http://127.0.0.1:8765`.

All recorded data stays on your machine in a local SQLite database (`data/clacktivity.db`). Nothing is sent over the network.

## What it does

### Visual keyboard heatmap
See which keys you press most on an interactive keyboard layout. You can switch between 100% Full-size, 80% TKL, 75%, and 60% US ANSI layouts, watch keys light up in real time as you type, and click any keycap to filter the logs below.

### Typing speed and daily activity
Track your daily keystroke count, unique keys pressed, active typing time, and typing speed (both average active WPM and peak WPM). A 24-hour chart breaks down your typing volume by hour of the day.

### Per-app and shortcut breakdown
See which applications (`Code.exe`, `chrome.exe`, and others) get the most keystrokes and check the top 5 keys pressed inside each app. The dashboard also tracks your most frequent modifier shortcuts such as `Ctrl+C`, `Ctrl+V`, and `Alt+Tab`.

### Live key stream and raw event log
Inspect your typing history in two synchronized views:
- A horizontal key stream (`250` events per page) with a `1:1 Raw` mode and a `Readable` mode that hides standalone modifier presses and breaks lines on `Enter`.
- A searchable raw event table (`100` events per page) with millisecond timestamps, active modifiers, and window titles.

Clicking any key, shortcut, or application in the dashboard filters both views at the same time.

### System tray controls and export
Pause or resume recording anytime from the Windows System Tray icon. You can also export your data for a single day or a custom date range as Raw CSV, Daily Summary CSV, or JSON.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer (only required if running from source)

## Getting started

### Option 1: Download the Windows executable (no Python required)

1. Go to the [Releases](https://github.com/faarismuda/Clacktivity/releases) page and download `Clacktivity-windows-x64.zip` (or `Clacktivity.exe`).
2. Run `Clacktivity.exe`.
3. The app starts in your Windows System Tray and opens the dashboard at `http://127.0.0.1:8765`.

### Option 2: Run from source with Python

```powershell
# 1. Clone the repository
git clone https://github.com/faarismuda/Clacktivity.git
cd Clacktivity

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application
python run.py
```

Running `python run.py` starts the background service, adds an icon to your Windows System Tray, and opens the dashboard at `http://127.0.0.1:8765`.

If the app is already running, running `python run.py` again simply opens the dashboard in your browser. You can also start it without a console window using `pythonw run.py` (logs are saved to `data/app.log`).

### CLI options

```powershell
python run.py [options]
```

| Flag | Description |
| :--- | :--- |
| `--host HOST` | Bind address for the web server (default: `127.0.0.1`) |
| `--port PORT` | Bind port for the web server (default: `8765`) |
| `--foreground` | Run attached to the current terminal instead of spawning a background process |
| `--no-tray` | Run without the Windows System Tray icon |
| `--no-browser` | Do not open the browser automatically on startup |
| `--no-hook` | Run the web server without the Windows keyboard hook (useful for frontend work) |

## Project structure

| Path | Purpose |
| :--- | :--- |
| `run.py` | CLI entrypoint and background process launcher |
| `src/hook.py` | Win32 keyboard listener thread (`WH_KEYBOARD_LL`) |
| `src/keymap.py` | Virtual-key and scan-code normalization |
| `src/window_tracker.py` | Foreground window title and executable lookup |
| `src/collector.py` | Modifier state tracking, event batching, and live WebSocket broadcast |
| `src/database.py` | SQLite storage and query layer |
| `src/analytics.py` | Daily stats, WPM calculations, and per-app aggregation |
| `src/exporter.py` | CSV and JSON data export |
| `src/api.py` | FastAPI REST routes and `/ws/live` WebSocket endpoint |
| `src/tray.py` | Windows System Tray icon and menu (`pystray` and `Pillow`) |
| `static/` | Vanilla HTML, CSS, and ES module JavaScript frontend |
| `tests/` | Automated test suite (`pytest`) |

## Running tests

```powershell
pytest -v
```

## Contributing

Contributions, bug reports, and feature ideas are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and pull request guidelines.

## License

This project is licensed under the [MIT License](LICENSE).
