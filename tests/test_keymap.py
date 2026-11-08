from src.keymap import resolve_vk, format_modifiers, format_combo


def test_resolve_alpha_and_digits():
    info_a = resolve_vk(0x41)
    assert info_a.key_code == "KeyA"
    assert info_a.key_label == "A"
    assert info_a.is_printable is True
    assert info_a.modifier_group is None

    info_1 = resolve_vk(0x31)
    assert info_1.key_code == "Digit1"
    assert info_1.key_label == "1"
    assert info_1.is_printable is True


def test_resolve_modifiers_and_navigation():
    lctrl = resolve_vk(0xA2)
    assert lctrl.key_code == "LeftControl"
    assert lctrl.modifier_group == "Ctrl"
    assert lctrl.is_printable is False

    space = resolve_vk(0x20)
    assert space.key_code == "Space"
    assert space.is_printable is True

    numpad_enter = resolve_vk(0x0D, flags=0x01)
    assert numpad_enter.key_code == "NumpadEnter"

    std_enter = resolve_vk(0x0D, flags=0x00)
    assert std_enter.key_code == "Enter"


def test_format_modifiers_and_combo():
    mods = {"Shift", "Ctrl"}
    assert format_modifiers(mods) == "Ctrl+Shift"
    key_c = resolve_vk(0x43)
    assert format_combo(mods, key_c) == "Ctrl+Shift+C"
    lctrl = resolve_vk(0xA2)
    assert format_combo(mods, lctrl) == ""
