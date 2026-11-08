/**
 * US ANSI Keyboard Layout Definitions: 100% (Full-size), 80% (TKL), 75%, and 60%.
 * Row key item: [key_code, label, width_units, gap_before_units (optional)]
 * Numpad grid item: { code, label, row, col, rowSpan?, colSpan? }
 */

const ROW_FN_MAIN = [
  ["Escape", "Esc", 1],
  ["F1", "F1", 1, 1], ["F2", "F2", 1], ["F3", "F3", 1], ["F4", "F4", 1],
  ["F5", "F5", 1, 0.5], ["F6", "F6", 1], ["F7", "F7", 1], ["F8", "F8", 1],
  ["F9", "F9", 1, 0.5], ["F10", "F10", 1], ["F11", "F11", 1], ["F12", "F12", 1],
];

const ROW_NUM = [
  ["Backquote", "`", 1], ["Digit1", "1", 1], ["Digit2", "2", 1], ["Digit3", "3", 1],
  ["Digit4", "4", 1], ["Digit5", "5", 1], ["Digit6", "6", 1], ["Digit7", "7", 1],
  ["Digit8", "8", 1], ["Digit9", "9", 1], ["Digit0", "0", 1], ["Minus", "-", 1],
  ["Equal", "=", 1], ["Backspace", "Backspace", 2],
];

const ROW_QWERTY = [
  ["Tab", "Tab", 1.5], ["KeyQ", "Q", 1], ["KeyW", "W", 1], ["KeyE", "E", 1],
  ["KeyR", "R", 1], ["KeyT", "T", 1], ["KeyY", "Y", 1], ["KeyU", "U", 1],
  ["KeyI", "I", 1], ["KeyO", "O", 1], ["KeyP", "P", 1], ["BracketLeft", "[", 1],
  ["BracketRight", "]", 1], ["Backslash", "\\", 1.5],
];

const ROW_HOME = [
  ["CapsLock", "Caps", 1.75], ["KeyA", "A", 1], ["KeyS", "S", 1], ["KeyD", "D", 1],
  ["KeyF", "F", 1], ["KeyG", "G", 1], ["KeyH", "H", 1], ["KeyJ", "J", 1],
  ["KeyK", "K", 1], ["KeyL", "L", 1], ["Semicolon", ";", 1], ["Quote", "'", 1],
  ["Enter", "Enter", 2.25],
];

const ROW_SHIFT = [
  ["LeftShift", "Shift", 2.25], ["KeyZ", "Z", 1], ["KeyX", "X", 1], ["KeyC", "C", 1],
  ["KeyV", "V", 1], ["KeyB", "B", 1], ["KeyN", "N", 1], ["KeyM", "M", 1],
  ["Comma", ",", 1], ["Period", ".", 1], ["Slash", "/", 1], ["RightShift", "Shift", 2.75],
];

const ROW_BOTTOM = [
  ["LeftControl", "Ctrl", 1.25], ["LeftWin", "Win", 1.25], ["LeftAlt", "Alt", 1.25],
  ["Space", "Space", 6.25],
  ["RightAlt", "Alt", 1.25], ["RightWin", "Win", 1.25], ["ContextMenu", "Menu", 1.25],
  ["RightControl", "Ctrl", 1.25],
];

const NAV_ROWS = [
  [["PrintScreen", "PrtSc", 1], ["ScrollLock", "ScrLk", 1], ["Pause", "Pause", 1]],
  [["Insert", "Ins", 1], ["Home", "Home", 1], ["PageUp", "PgUp", 1]],
  [["Delete", "Del", 1], ["End", "End", 1], ["PageDown", "PgDn", 1]],
  [],
  [["ArrowUp", "Up", 1, 1]],
  [["ArrowLeft", "Left", 1], ["ArrowDown", "Down", 1], ["ArrowRight", "Right", 1]],
];

const NUMPAD_KEYS = [
  { code: "NumLock", label: "NumLk", row: 2, col: 1 },
  { code: "NumpadDivide", label: "Num /", row: 2, col: 2 },
  { code: "NumpadMultiply", label: "Num *", row: 2, col: 3 },
  { code: "NumpadSubtract", label: "Num -", row: 2, col: 4 },

  { code: "Numpad7", label: "Num 7", row: 3, col: 1 },
  { code: "Numpad8", label: "Num 8", row: 3, col: 2 },
  { code: "Numpad9", label: "Num 9", row: 3, col: 3 },
  { code: "NumpadAdd", label: "Num +", row: 3, col: 4, rowSpan: 2 },

  { code: "Numpad4", label: "Num 4", row: 4, col: 1 },
  { code: "Numpad5", label: "Num 5", row: 4, col: 2 },
  { code: "Numpad6", label: "Num 6", row: 4, col: 3 },

  { code: "Numpad1", label: "Num 1", row: 5, col: 1 },
  { code: "Numpad2", label: "Num 2", row: 5, col: 2 },
  { code: "Numpad3", label: "Num 3", row: 5, col: 3 },
  { code: "NumpadEnter", label: "Num Ent", row: 5, col: 4, rowSpan: 2 },

  { code: "Numpad0", label: "Num 0", row: 6, col: 1, colSpan: 2 },
  { code: "NumpadDecimal", label: "Num .", row: 6, col: 3 },
];

export const KEYBOARD_LAYOUTS = {
  "100": {
    name: "100% Full-Size",
    mainRows: [ROW_FN_MAIN, ROW_NUM, ROW_QWERTY, ROW_HOME, ROW_SHIFT, ROW_BOTTOM],
    navRows: NAV_ROWS,
    numpad: NUMPAD_KEYS,
  },
  "80": {
    name: "80% Tenkeyless (TKL)",
    mainRows: [ROW_FN_MAIN, ROW_NUM, ROW_QWERTY, ROW_HOME, ROW_SHIFT, ROW_BOTTOM],
    navRows: NAV_ROWS,
  },
  "75": {
    name: "75% Compact",
    mainRows: [
      [
        ["Escape", "Esc", 1], ["F1", "F1", 1], ["F2", "F2", 1], ["F3", "F3", 1],
        ["F4", "F4", 1], ["F5", "F5", 1], ["F6", "F6", 1], ["F7", "F7", 1],
        ["F8", "F8", 1], ["F9", "F9", 1], ["F10", "F10", 1], ["F11", "F11", 1],
        ["F12", "F12", 1], ["PrintScreen", "PrtSc", 1], ["Insert", "Ins", 1], ["Delete", "Del", 1],
      ],
      [...ROW_NUM, ["Home", "Home", 1]],
      [...ROW_QWERTY, ["PageUp", "PgUp", 1]],
      [...ROW_HOME, ["PageDown", "PgDn", 1]],
      [
        ["LeftShift", "Shift", 2.25], ["KeyZ", "Z", 1], ["KeyX", "X", 1], ["KeyC", "C", 1],
        ["KeyV", "V", 1], ["KeyB", "B", 1], ["KeyN", "N", 1], ["KeyM", "M", 1],
        ["Comma", ",", 1], ["Period", ".", 1], ["Slash", "/", 1],
        ["RightShift", "Shift", 1.75], ["ArrowUp", "Up", 1], ["End", "End", 1],
      ],
      [
        ["LeftControl", "Ctrl", 1.25], ["LeftWin", "Win", 1.25], ["LeftAlt", "Alt", 1.25],
        ["Space", "Space", 6.25],
        ["RightAlt", "Alt", 1], ["ContextMenu", "Menu", 1], ["RightControl", "Ctrl", 1],
        ["ArrowLeft", "Left", 1], ["ArrowDown", "Down", 1], ["ArrowRight", "Right", 1],
      ],
    ],
  },
  "60": {
    name: "60% Mini",
    mainRows: [
      [["Escape", "Esc", 1], ...ROW_NUM.slice(1)],
      ROW_QWERTY,
      ROW_HOME,
      ROW_SHIFT,
      ROW_BOTTOM,
    ],
  },
};
