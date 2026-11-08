"""Asynchronous event collector, modifier state tracker, and SQLite batch writer."""

from collections.abc import Callable
from datetime import datetime
import queue
import threading
from typing import Any

from src.database import Database
from src.hook import RawKeyEvent
from src.keymap import format_combo, format_modifiers, resolve_vk
from src.window_tracker import get_active_window_info


class EventCollector:
    """Processes raw key events, tracks modifier state, batches DB inserts, and broadcasts."""

    def __init__(
        self,
        db: Database,
        window_provider: Callable[[], tuple[str, str]] = get_active_window_info,
        batch_interval_sec: float = 0.25,
        batch_max_size: int = 50,
    ) -> None:
        self.db = db
        self._window_provider = window_provider
        self._batch_interval_sec = batch_interval_sec
        self._batch_max_size = batch_max_size

        self._raw_queue: queue.SimpleQueue[RawKeyEvent | None] = queue.SimpleQueue()
        self._pending_batch: list[dict[str, Any]] = []
        self._batch_lock = threading.Lock()
        self._held_modifier_keys: dict[str, str] = {}
        self._active_modifiers: set[str] = set()
        self._is_paused = False
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []
        self._sub_lock = threading.Lock()
        self._worker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def is_paused(self) -> bool:
        """Return whether key event recording is currently paused."""
        return self._is_paused

    def set_paused(self, paused: bool) -> bool:
        """Set pause state and clear active modifiers when pausing."""
        self._is_paused = bool(paused)
        if self._is_paused:
            self._held_modifier_keys.clear()
            self._active_modifiers.clear()
        self._notify_subscribers({"type": "status", "is_paused": self._is_paused})
        return self._is_paused

    def toggle_paused(self) -> bool:
        """Toggle pause state and return the new is_paused boolean."""
        return self.set_paused(not self._is_paused)

    def subscribe(self, callback: Callable[[dict[str, Any]], None]) -> Callable[[], None]:
        """Register a listener for live key events and status changes."""
        with self._sub_lock:
            self._subscribers.append(callback)

        def _unsubscribe() -> None:
            with self._sub_lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return _unsubscribe

    def _notify_subscribers(self, payload: dict[str, Any]) -> None:
        with self._sub_lock:
            listeners = list(self._subscribers)
        for fn in listeners:
            try:
                fn(payload)
            except Exception:
                pass

    def enqueue(self, raw: RawKeyEvent) -> None:
        """Non-blocking enqueue called directly by the Win32 hook callback."""
        self._raw_queue.put(raw)

    def handle_raw_event(self, raw: RawKeyEvent) -> dict[str, Any] | None:
        """Process a single RawKeyEvent synchronously (updates modifiers & buffers record)."""
        key_info = resolve_vk(raw.vk_code, raw.flags)

        if not raw.is_keydown:
            if key_info.modifier_group:
                self._held_modifier_keys.pop(key_info.key_code, None)
                if key_info.modifier_group not in self._held_modifier_keys.values():
                    self._active_modifiers.discard(key_info.modifier_group)
            return None

        if self._is_paused:
            return None

        if key_info.modifier_group:
            self._held_modifier_keys[key_info.key_code] = key_info.modifier_group
            self._active_modifiers.add(key_info.modifier_group)

        dt = datetime.fromtimestamp(raw.timestamp)
        iso_time = dt.strftime("%Y-%m-%d %H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}"
        date_str = dt.strftime("%Y-%m-%d")
        hour = dt.hour

        app_name, window_title = self._window_provider()
        modifiers_str = format_modifiers(self._active_modifiers)
        combo_str = format_combo(self._active_modifiers, key_info)

        record: dict[str, Any] = {
            "timestamp": raw.timestamp,
            "iso_time": iso_time,
            "date_str": date_str,
            "hour": hour,
            "vk_code": raw.vk_code,
            "key_code": key_info.key_code,
            "key_label": key_info.key_label,
            "modifiers": modifiers_str,
            "combo_label": combo_str,
            "is_printable": 1 if key_info.is_printable else 0,
            "app_name": app_name,
            "window_title": window_title,
        }

        with self._batch_lock:
            self._pending_batch.append(record)
            should_flush = len(self._pending_batch) >= self._batch_max_size

        if should_flush:
            self.flush()

        self._notify_subscribers({"type": "key_event", "event": record})
        return record

    def flush(self) -> int:
        """Write any buffered key events to SQLite immediately."""
        with self._batch_lock:
            if not self._pending_batch:
                return 0
            batch = self._pending_batch
            self._pending_batch = []
        return self.db.insert_events_batch(batch)

    def start_worker(self) -> None:
        """Start the background queue consumer and periodic SQLite flusher thread."""
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(
            target=self._worker_loop, name="CollectorWorker", daemon=True
        )
        self._worker_thread.start()

    def stop_worker(self) -> None:
        """Stop the background worker thread and flush remaining events."""
        self._stop_event.set()
        self._raw_queue.put(None)
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        self.flush()

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._raw_queue.get(timeout=self._batch_interval_sec)
                if item is None:
                    break
                self.handle_raw_event(item)
            except queue.Empty:
                self.flush()
        self.flush()
