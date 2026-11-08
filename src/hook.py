"""Win32 low-level keyboard hook (WH_KEYBOARD_LL) running on a dedicated thread."""

from collections.abc import Callable
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import threading
import time

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

LRESULT = ctypes.c_ssize_t
HHOOK = ctypes.c_void_p
ULONG_PTR = ctypes.c_size_t


class KBDLLHOOKSTRUCT(ctypes.Structure):
    """Win32 KBDLLHOOKSTRUCT passed via lParam in WH_KEYBOARD_LL callbacks."""

    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    HOOKPROC,
    wintypes.HINSTANCE,
    wintypes.DWORD,
]
user32.SetWindowsHookExW.restype = HHOOK
user32.CallNextHookEx.argtypes = [HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = [HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]
user32.GetMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.PostThreadMessageW.restype = wintypes.BOOL
kernel32.GetCurrentThreadId.argtypes = []
kernel32.GetCurrentThreadId.restype = wintypes.DWORD


@dataclass(frozen=True)
class RawKeyEvent:
    """Minimal raw key event captured inside the low-level hook callback."""

    timestamp: float
    vk_code: int
    flags: int
    is_keydown: bool


class Win32KeyboardHook:
    """Manages a dedicated Win32 message-pump thread for WH_KEYBOARD_LL."""

    def __init__(self, on_event: Callable[[RawKeyEvent], None]) -> None:
        self._on_event = on_event
        self._thread: threading.Thread | None = None
        self._thread_id: int = 0
        self._hook_handle: HHOOK | None = None
        self._hook_proc_ref: HOOKPROC | None = None
        self._ready = threading.Event()

    def start(self) -> None:
        """Start the background Win32 keyboard hook thread."""
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="Win32KeyboardHook", daemon=True
        )
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def stop(self) -> None:
        """Post WM_QUIT to the hook message loop and wait for clean shutdown."""
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._thread_id = 0

    def _run_loop(self) -> None:
        self._thread_id = int(kernel32.GetCurrentThreadId())

        def _callback(n_code: int, w_param: int, l_param: int) -> int:
            if n_code >= 0 and l_param:
                if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP):
                    kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                    is_down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                    try:
                        self._on_event(
                            RawKeyEvent(
                                timestamp=time.time(),
                                vk_code=int(kb.vkCode),
                                flags=int(kb.flags),
                                is_keydown=is_down,
                            )
                        )
                    except Exception:
                        pass
            return user32.CallNextHookEx(self._hook_handle, n_code, w_param, l_param)

        self._hook_proc_ref = HOOKPROC(_callback)
        self._hook_handle = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._hook_proc_ref, None, 0
        )
        self._ready.set()

        if not self._hook_handle:
            return

        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                pass
        finally:
            if self._hook_handle:
                user32.UnhookWindowsHookEx(self._hook_handle)
                self._hook_handle = None
