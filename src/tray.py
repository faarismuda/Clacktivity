"""Windows System Tray controller using pystray and Pillow."""

from collections.abc import Callable
from typing import Any
import webbrowser

from PIL import Image, ImageDraw
import pystray

from src.collector import EventCollector


def create_tray_icon_image(is_paused: bool = False) -> Image.Image:
    """Generate a 64x64 keyboard icon with a live/paused status badge."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer keyboard body
    draw.rounded_rectangle(
        (4, 12, 60, 52),
        radius=8,
        fill=(28, 30, 36, 255),
        outline=(90, 96, 110, 255),
        width=2,
    )

    # Keycap grid rows
    key_color = (210, 214, 224, 255)
    for row_idx, y in enumerate((19, 28)):
        for col_idx in range(5):
            x = 11 + col_idx * 9
            draw.rectangle((x, y, x + 6, y + 5), fill=key_color)

    # Spacebar row
    draw.rectangle((11, 38, 17, 44), fill=key_color)
    draw.rectangle((20, 38, 44, 44), fill=(245, 158, 11, 255))
    draw.rectangle((47, 38, 53, 44), fill=key_color)

    # Status indicator circle in bottom-right corner
    badge_fill = (245, 158, 11, 255) if is_paused else (34, 197, 94, 255)
    draw.ellipse(
        (44, 40, 62, 58),
        fill=badge_fill,
        outline=(20, 22, 26, 255),
        width=3,
    )
    return img


class SystemTrayApp:
    """Manages the Windows System Tray icon and context menu actions."""

    def __init__(
        self,
        collector: EventCollector,
        dashboard_url: str,
        on_quit: Callable[[], None],
    ) -> None:
        self.collector = collector
        self.dashboard_url = dashboard_url
        self.on_quit = on_quit
        self._icon: pystray.Icon | None = None
        self._unsubscribe = self.collector.subscribe(self._on_collector_event)

    def _on_collector_event(self, payload: dict[str, Any]) -> None:
        if payload.get("type") == "status" and self._icon is not None:
            paused = bool(payload.get("is_paused", False))
            self._icon.icon = create_tray_icon_image(is_paused=paused)
            self._icon.title = (
                "Clacktivity (Paused)"
                if paused
                else "Clacktivity (Recording)"
            )
            self._icon.update_menu()

    def _open_dashboard(self, _icon: Any = None, _item: Any = None) -> None:
        webbrowser.open(self.dashboard_url)

    def _toggle_pause(self, _icon: Any = None, _item: Any = None) -> None:
        self.collector.toggle_paused()

    def _quit_app(self, _icon: Any = None, _item: Any = None) -> None:
        self._unsubscribe()
        if self._icon is not None:
            self._icon.stop()
        self.on_quit()

    def run(self) -> None:
        """Run the blocking system tray loop on the calling thread."""
        menu = pystray.Menu(
            pystray.MenuItem("Open Dashboard", self._open_dashboard, default=True),
            pystray.MenuItem(
                lambda _item: (
                    "Resume Recording"
                    if self.collector.is_paused
                    else "Pause Recording"
                ),
                self._toggle_pause,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_app),
        )
        self._icon = pystray.Icon(
            name="Clacktivity",
            icon=create_tray_icon_image(is_paused=self.collector.is_paused),
            title="Clacktivity (Recording)",
            menu=menu,
        )
        self._icon.run()

    def stop(self) -> None:
        """Stop the system tray icon if running."""
        self._unsubscribe()
        if self._icon is not None:
            self._icon.stop()
