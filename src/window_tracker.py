"""Win32 foreground window and process executable name resolver."""

import ctypes
from ctypes import wintypes
from pathlib import Path

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def get_active_window_info() -> tuple[str, str]:
    """Return (app_name, window_title) of the current foreground window on Windows."""
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ("Desktop", "")

        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            title_buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buf, length + 1)
            title = title_buf.value.strip()

        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return ("Unknown", title)

        h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not h_proc:
            return ("System", title)

        try:
            buf_len = wintypes.DWORD(1024)
            exe_buf = ctypes.create_unicode_buffer(buf_len.value)
            ok = kernel32.QueryFullProcessImageNameW(
                h_proc, 0, exe_buf, ctypes.byref(buf_len)
            )
            if ok and exe_buf.value:
                app_name = Path(exe_buf.value).name
                return (app_name or "Unknown", title)
        finally:
            kernel32.CloseHandle(h_proc)

        return ("Unknown", title)
    except Exception:
        return ("Unknown", "")
