"""Windows Virtual-Key (VK) mapping to canonical keyboard layout codes."""

from dataclasses import dataclass

LLKHF_EXTENDED = 0x01
MODIFIER_ORDER = ("Ctrl", "Alt", "Shift", "Win")


@dataclass(frozen=True)
class KeyInfo:
    """Normalized representation of a keyboard key."""

    vk_code: int
    key_code: str
    key_label: str
    is_printable: bool
    modifier_group: str | None = None


_SPECIAL_KEYS: dict[int, tuple[str, str, bool, str | None]] = {
    0x08: ("Backspace", "Backspace", False, None),
    0x09: ("Tab", "Tab", False, None),
    0x0C: ("NumpadClear", "Clear", False, None),
    0x0D: ("Enter", "Enter", False, None),
    0x10: ("LeftShift", "Shift", False, "Shift"),
    0x11: ("LeftControl", "Ctrl", False, "Ctrl"),
    0x12: ("LeftAlt", "Alt", False, "Alt"),
    0x13: ("Pause", "Pause", False, None),
    0x14: ("CapsLock", "Caps Lock", False, None),
    0x1B: ("Escape", "Esc", False, None),
    0x20: ("Space", "Space", True, None),
    0x21: ("PageUp", "PgUp", False, None),
    0x22: ("PageDown", "PgDn", False, None),
    0x23: ("End", "End", False, None),
    0x24: ("Home", "Home", False, None),
    0x25: ("ArrowLeft", "Left", False, None),
    0x26: ("ArrowUp", "Up", False, None),
    0x27: ("ArrowRight", "Right", False, None),
    0x28: ("ArrowDown", "Down", False, None),
    0x2C: ("PrintScreen", "PrtSc", False, None),
    0x2D: ("Insert", "Ins", False, None),
    0x2E: ("Delete", "Del", False, None),
    0x5B: ("LeftWin", "Win", False, "Win"),
    0x5C: ("RightWin", "RWin", False, "Win"),
    0x5D: ("ContextMenu", "Menu", False, None),
    0x6A: ("NumpadMultiply", "Num *", True, None),
    0x6B: ("NumpadAdd", "Num +", True, None),
    0x6D: ("NumpadSubtract", "Num -", True, None),
    0x6E: ("NumpadDecimal", "Num .", True, None),
    0x6F: ("NumpadDivide", "Num /", True, None),
    0x90: ("NumLock", "Num Lock", False, None),
    0x91: ("ScrollLock", "ScrLk", False, None),
    0xA0: ("LeftShift", "LShift", False, "Shift"),
    0xA1: ("RightShift", "RShift", False, "Shift"),
    0xA2: ("LeftControl", "LCtrl", False, "Ctrl"),
    0xA3: ("RightControl", "RCtrl", False, "Ctrl"),
    0xA4: ("LeftAlt", "LAlt", False, "Alt"),
    0xA5: ("RightAlt", "RAlt", False, "Alt"),
    0xBA: ("Semicolon", ";", True, None),
    0xBB: ("Equal", "=", True, None),
    0xBC: ("Comma", ",", True, None),
    0xBD: ("Minus", "-", True, None),
    0xBE: ("Period", ".", True, None),
    0xBF: ("Slash", "/", True, None),
    0xC0: ("Backquote", "`", True, None),
    0xDB: ("BracketLeft", "[", True, None),
    0xDC: ("Backslash", "\\", True, None),
    0xDD: ("BracketRight", "]", True, None),
    0xDE: ("Quote", "'", True, None),
}


def resolve_vk(vk_code: int, flags: int = 0) -> KeyInfo:
    """Resolve a Windows Virtual-Key code and LLKHF flags to canonical KeyInfo."""
    is_extended = bool(flags & LLKHF_EXTENDED)

    if vk_code == 0x0D and is_extended:
        return KeyInfo(vk_code, "NumpadEnter", "Num Enter", False, None)

    if 0x41 <= vk_code <= 0x5A:
        ch = chr(vk_code)
        return KeyInfo(vk_code, f"Key{ch}", ch, True, None)

    if 0x30 <= vk_code <= 0x39:
        digit = chr(vk_code)
        return KeyInfo(vk_code, f"Digit{digit}", digit, True, None)

    if 0x60 <= vk_code <= 0x69:
        num = vk_code - 0x60
        return KeyInfo(vk_code, f"Numpad{num}", f"Num {num}", True, None)

    if 0x70 <= vk_code <= 0x87:
        fn_idx = vk_code - 0x70 + 1
        return KeyInfo(vk_code, f"F{fn_idx}", f"F{fn_idx}", False, None)

    if vk_code in _SPECIAL_KEYS:
        code, label, printable, mod_group = _SPECIAL_KEYS[vk_code]
        return KeyInfo(vk_code, code, label, printable, mod_group)

    return KeyInfo(vk_code, f"VK_{vk_code:02X}", f"0x{vk_code:02X}", False, None)


def format_modifiers(active_modifiers: set[str]) -> str:
    """Format active modifier names in canonical Ctrl+Alt+Shift+Win order."""
    if not active_modifiers:
        return ""
    ordered = [m for m in MODIFIER_ORDER if m in active_modifiers]
    return "+".join(ordered)


def format_combo(active_modifiers: set[str], key_info: KeyInfo) -> str:
    """Format a shortcut combination when a non-modifier key is pressed with modifiers."""
    if key_info.modifier_group is not None or not active_modifiers:
        return ""
    mod_str = format_modifiers(active_modifiers)
    if not mod_str:
        return ""
    return f"{mod_str}+{key_info.key_label}"
