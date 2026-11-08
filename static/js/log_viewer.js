/**
 * Renderers for the Daily All-Keys Summary Table and the Sequential Raw Event Log.
 */

import { escapeHtml } from "./charts.js";

export function renderDailyKeysTable(tbodyEl, allKeys, onKeyClick, selectedKey = "", filterText = "") {
  if (!tbodyEl) return;
  const query = filterText.trim().toLowerCase();
  const filtered = (allKeys || []).filter((item) => {
    if (!query) return true;
    return (
      item.key_label.toLowerCase().includes(query) ||
      item.key_code.toLowerCase().includes(query)
    );
  });

  if (filtered.length === 0) {
    tbodyEl.innerHTML = `<tr><td colspan="4" class="empty-cell">No matching keys pressed on this date.</td></tr>`;
    return;
  }

  tbodyEl.innerHTML = filtered
    .map((item, idx) => {
      const isSelected = selectedKey === item.key_code;
      return `
        <tr class="data-tr ${isSelected ? "data-tr-selected" : ""}" data-key-code="${escapeHtml(item.key_code)}">
          <td class="num-col">${idx + 1}</td>
          <td><span class="key-badge">${escapeHtml(item.key_label)}</span></td>
          <td class="mono-col">${escapeHtml(item.key_code)}</td>
          <td class="num-col"><strong>${item.count.toLocaleString()}</strong> <span class="muted">(${item.percentage}%)</span></td>
        </tr>
      `;
    })
    .join("");

  tbodyEl.querySelectorAll("tr[data-key-code]").forEach((tr) => {
    tr.addEventListener("click", () => {
      if (onKeyClick) onKeyClick(tr.dataset.keyCode);
    });
  });
}

export function renderRawEventsTable(tbodyEl, events) {
  if (!tbodyEl) return;
  if (!events || events.length === 0) {
    tbodyEl.innerHTML = `<tr><td colspan="5" class="empty-cell">No raw press events match the current filter.</td></tr>`;
    return;
  }

  tbodyEl.innerHTML = events
    .map((ev) => buildRawEventRowHtml(ev))
    .join("");
}

export function prependLiveEventRow(tbodyEl, ev, maxRows = 100) {
  if (!tbodyEl) return;
  const emptyCell = tbodyEl.querySelector(".empty-cell");
  if (emptyCell) {
    tbodyEl.innerHTML = "";
  }
  const temp = document.createElement("tbody");
  temp.innerHTML = buildRawEventRowHtml(ev, true);
  const newRow = temp.firstElementChild;
  if (newRow) {
    tbodyEl.insertBefore(newRow, tbodyEl.firstChild);
    while (tbodyEl.children.length > maxRows) {
      tbodyEl.removeChild(tbodyEl.lastElementChild);
    }
  }
}

function buildRawEventRowHtml(ev, isLive = false) {
  const timePart = String(ev.iso_time || "").split(" ")[1] || ev.iso_time || "";
  const comboHtml = ev.combo_label
    ? `<span class="combo-badge">${escapeHtml(ev.combo_label)}</span>`
    : ev.modifiers
      ? `<span class="mod-pill">${escapeHtml(ev.modifiers)}</span>`
      : `<span class="muted">-</span>`;

  return `
    <tr class="data-tr ${isLive ? "row-live-enter" : ""}">
      <td class="mono-col">${escapeHtml(timePart)}</td>
      <td><span class="key-badge">${escapeHtml(ev.key_label)}</span> <span class="muted mono-sm">${escapeHtml(ev.key_code)}</span></td>
      <td>${comboHtml}</td>
      <td class="mono-col">${escapeHtml(ev.app_name || "Unknown")}</td>
      <td class="truncate-col" title="${escapeHtml(ev.window_title || "")}">${escapeHtml(ev.window_title || "-")}</td>
    </tr>
  `;
}

export function renderHorizontalEventsStream(containerEl, events, order = "asc", mode = "raw") {
  if (!containerEl) return;
  const filtered = (events || []).filter((ev) => !(mode === "clean" && !ev.combo_label && ev.modifiers));
  if (filtered.length === 0) {
    containerEl.innerHTML = `<div class="empty-cell" style="width:100%;">No raw press events match the current filter.</div>`;
    return;
  }

  const ordered = order === "asc" ? [...filtered].reverse() : [...filtered];
  containerEl.innerHTML = ordered
    .map((ev) => buildStreamEventChipHtml(ev, false, mode))
    .join("");
}

export function insertLiveStreamChip(containerEl, ev, order = "asc", maxItems = 250, mode = "raw") {
  if (!containerEl) return;
  if (mode === "clean" && !ev.combo_label && ev.modifiers) return;
  const emptyCell = containerEl.querySelector(".empty-cell");
  if (emptyCell) {
    containerEl.innerHTML = "";
  }
  const temp = document.createElement("div");
  temp.innerHTML = buildStreamEventChipHtml(ev, true, mode);
  const nodes = Array.from(temp.children);
  if (nodes.length === 0) return;
  const newChip = nodes[0];
  setTimeout(() => newChip.classList.remove("stream-chip-live"), 900);

  if (order === "asc") {
    nodes.forEach((n) => containerEl.appendChild(n));
    while (containerEl.querySelectorAll(".stream-chip").length > maxItems) {
      const first = containerEl.firstElementChild;
      if (!first) break;
      containerEl.removeChild(first);
      if (containerEl.firstElementChild?.classList.contains("stream-line-break")) {
        containerEl.removeChild(containerEl.firstElementChild);
      }
    }
    containerEl.scrollTop = containerEl.scrollHeight;
  } else {
    for (let i = nodes.length - 1; i >= 0; i--) {
      containerEl.insertBefore(nodes[i], containerEl.firstChild);
    }
    while (containerEl.querySelectorAll(".stream-chip").length > maxItems) {
      const last = containerEl.lastElementChild;
      if (!last) break;
      containerEl.removeChild(last);
    }
  }
}

function buildStreamEventChipHtml(ev, isLive = false, mode = "raw") {
  const timePart = String(ev.iso_time || "").split(" ")[1] || ev.iso_time || "";
  const liveClass = isLive ? " stream-chip-live" : "";
  const comboInfo = ev.combo_label
    ? ` | Combo: ${ev.combo_label}`
    : ev.modifiers
      ? ` | Mod: ${ev.modifiers}`
      : "";
  const tooltip = `${timePart} | Key: ${ev.key_label} (${ev.key_code})${comboInfo} | App: ${ev.app_name || "Unknown"} | Window: ${ev.window_title || "-"}`;
  const lineBreak = mode === "clean" && (ev.key_code === "Enter" || ev.key_code === "NumpadEnter")
    ? `<span class="stream-line-break"></span>`
    : "";

  if (ev.combo_label) {
    return `<span class="combo-badge stream-chip${liveClass}" title="${escapeHtml(tooltip)}">${escapeHtml(ev.combo_label)}</span>${lineBreak}`;
  }
  if (ev.modifiers) {
    return `<span class="mod-pill stream-chip${liveClass}" title="${escapeHtml(tooltip)}">${escapeHtml(ev.key_label)}</span>${lineBreak}`;
  }
  return `<span class="key-badge stream-chip${liveClass}" title="${escapeHtml(tooltip)}">${escapeHtml(ev.key_label)}</span>${lineBreak}`;
}
