/**
 * Renderers for 24-hour activity chart, top keys, top shortcuts, and per-app analytics.
 */

export function renderHourlyChart(containerEl, hourlyCounts) {
  if (!containerEl) return;
  const counts = Array.isArray(hourlyCounts) && hourlyCounts.length === 24
    ? hourlyCounts
    : new Array(24).fill(0);
  const maxVal = Math.max(...counts, 1);

  containerEl.innerHTML = "";
  counts.forEach((cnt, hr) => {
    const pct = Math.max(cnt > 0 ? 6 : 1, Math.round((cnt / maxVal) * 100));
    const col = document.createElement("div");
    col.className = "hour-col";
    col.title = `${String(hr).padStart(2, "0")}:00 - ${cnt.toLocaleString()} keystrokes`;

    const barWrap = document.createElement("div");
    barWrap.className = "hour-bar-wrap";

    const bar = document.createElement("div");
    bar.className = cnt > 0 ? "hour-bar hour-bar-filled" : "hour-bar";
    bar.style.height = `${pct}%`;

    const label = document.createElement("span");
    label.className = "hour-label";
    label.textContent = hr % 3 === 0 ? `${String(hr).padStart(2, "0")}h` : "";

    barWrap.appendChild(bar);
    col.appendChild(barWrap);
    col.appendChild(label);
    containerEl.appendChild(col);
  });
}

export function renderTopKeysList(containerEl, topKeys, onKeyClick, selectedKey = "") {
  if (!containerEl) return;
  if (!topKeys || topKeys.length === 0) {
    containerEl.innerHTML = `<p class="empty-note">No keystrokes recorded on this date yet.</p>`;
    return;
  }

  const maxCount = Math.max(...topKeys.map((k) => k.count), 1);
  containerEl.innerHTML = "";

  for (const item of topKeys.slice(0, 10)) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = `rank-row ${selectedKey === item.key_code ? "rank-row-active" : ""}`;
    row.addEventListener("click", () => onKeyClick && onKeyClick(item.key_code));

    const barPct = Math.round((item.count / maxCount) * 100);
    row.innerHTML = `
      <div class="rank-row-top">
        <span class="key-badge">${escapeHtml(item.key_label)}</span>
        <span class="rank-code">${escapeHtml(item.key_code)}</span>
        <span class="rank-metric">${item.count.toLocaleString()} <small>(${item.percentage}%)</small></span>
      </div>
      <div class="rank-track"><div class="rank-fill" style="width:${barPct}%"></div></div>
    `;
    containerEl.appendChild(row);
  }
}

export function renderShortcutsList(containerEl, shortcuts) {
  if (!containerEl) return;
  if (!shortcuts || shortcuts.length === 0) {
    containerEl.innerHTML = `<p class="empty-note">No modifier shortcuts recorded on this date.</p>`;
    return;
  }

  const maxCount = Math.max(...shortcuts.map((s) => s.count), 1);
  containerEl.innerHTML = "";

  for (const item of shortcuts.slice(0, 10)) {
    const row = document.createElement("div");
    row.className = "rank-row rank-row-static";
    const barPct = Math.round((item.count / maxCount) * 100);
    row.innerHTML = `
      <div class="rank-row-top">
        <span class="combo-badge">${escapeHtml(item.combo)}</span>
        <span class="rank-metric">${item.count.toLocaleString()} <small>(${item.percentage}%)</small></span>
      </div>
      <div class="rank-track"><div class="rank-fill rank-fill-alt" style="width:${barPct}%"></div></div>
    `;
    containerEl.appendChild(row);
  }
}

export function renderAppsBreakdown(containerEl, apps, onAppClick, selectedApp = "") {
  if (!containerEl) return;
  if (!apps || apps.length === 0) {
    containerEl.innerHTML = `<p class="empty-note">No application activity recorded on this date.</p>`;
    return;
  }

  const maxCount = Math.max(...apps.map((a) => a.count), 1);
  containerEl.innerHTML = "";

  for (const app of apps.slice(0, 12)) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `app-row ${selectedApp === app.app_name ? "rank-row-active" : ""}`;
    card.addEventListener("click", () => onAppClick && onAppClick(app.app_name));

    const barPct = Math.round((app.count / maxCount) * 100);
    const pills = (app.top_keys || [])
      .map((k) => `<span class="mini-key">${escapeHtml(k.key_label)} <b>${k.count}</b></span>`)
      .join("");

    card.innerHTML = `
      <div class="rank-row-top">
        <span class="app-title">${escapeHtml(app.app_name)}</span>
        <span class="rank-metric">${app.count.toLocaleString()} <small>(${app.percentage}%)</small></span>
      </div>
      <div class="rank-track"><div class="rank-fill" style="width:${barPct}%"></div></div>
      <div class="app-keys-line">${pills}</div>
    `;
    containerEl.appendChild(card);
  }
}

export function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
