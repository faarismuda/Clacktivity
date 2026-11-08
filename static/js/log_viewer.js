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
