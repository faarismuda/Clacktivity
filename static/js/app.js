/**
 * Main Dashboard Controller: coordinates state, REST API calls, filters, and live WebSocket.
 */

import { KeyboardHeatmap } from "./heatmap.js";
import {
  renderAppsBreakdown,
  renderHourlyChart,
  renderShortcutsList,
  renderTopKeysList,
} from "./charts.js";
import {
  prependLiveEventRow,
  renderDailyKeysTable,
  renderRawEventsTable,
} from "./log_viewer.js";

const state = {
  today: "",
  selectedDate: "",
  availableDates: [],
  isPaused: false,
  selectedKey: "",
  selectedApp: "",
  keySearch: "",
  logSearch: "",
  logOffset: 0,
  logLimit: 100,
  logTotal: 0,
  dailyReport: null,
};

let heatmap = null;
let searchDebounce = null;
const $ = (id) => document.getElementById(id);

function formatDuration(seconds) {
  const sec = Math.round(Number(seconds) || 0);
  if (sec < 60) return `${sec}s`;
  const mins = Math.floor(sec / 60);
  return mins < 60 ? `${mins}m ${sec % 60}s` : `${Math.floor(mins / 60)}h ${mins % 60}m`;
}

async function initDashboard() {
  heatmap = new KeyboardHeatmap($("heatmap-container"), (keyCode) => {
    state.selectedKey = keyCode;
    state.logOffset = 0;
    refreshSelectionViews();
    loadRawEvents();
  });
  bindEvents();
  await loadStatusAndInitialData();
  connectWebSocket();
}

function bindEvents() {
  document.querySelectorAll("[data-layout]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-layout]").forEach((b) => b.classList.remove("seg-active"));
      btn.classList.add("seg-active");
      heatmap.setLayout(btn.dataset.layout);
    });
  });

  $("date-picker").addEventListener("change", (e) => e.target.value && selectDate(e.target.value));
  $("btn-today").addEventListener("click", () => state.today && selectDate(state.today));
  $("btn-refresh").addEventListener("click", () => { loadDailyAnalytics(); loadRawEvents(); });

  $("btn-toggle-pause").addEventListener("click", async () => {
    const res = await fetch("/api/status/toggle", { method: "POST" });
    if (res.ok) updatePauseBadge((await res.json()).is_paused);
  });

  $("key-table-search").addEventListener("input", (e) => {
    state.keySearch = e.target.value;
    if (state.dailyReport) {
      renderDailyKeysTable($("daily-keys-tbody"), state.dailyReport.all_keys, handleKeyFilterToggle, state.selectedKey, state.keySearch);
    }
  });

  $("log-search").addEventListener("input", (e) => {
    state.logSearch = e.target.value;
    state.logOffset = 0;
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(loadRawEvents, 200);
  });

  $("btn-clear-filters").addEventListener("click", () => {
    state.selectedKey = "";
    state.selectedApp = "";
    state.logSearch = "";
    $("log-search").value = "";
    state.logOffset = 0;
    heatmap.setCounts(state.dailyReport?.key_counts || {}, "");
    refreshSelectionViews();
    loadRawEvents();
  });

  $("btn-prev-page").addEventListener("click", () => {
    if (state.logOffset >= state.logLimit) { state.logOffset -= state.logLimit; loadRawEvents(); }
  });
  $("btn-next-page").addEventListener("click", () => {
    if (state.logOffset + state.logLimit < state.logTotal) { state.logOffset += state.logLimit; loadRawEvents(); }
  });

  $("btn-export-csv").addEventListener("click", () => triggerExport("csv", "raw"));
  $("btn-export-summary").addEventListener("click", () => triggerExport("csv", "summary"));
  $("btn-export-json").addEventListener("click", () => triggerExport("json", "raw"));
}

function triggerExport(fmt, mode) {
  const d = encodeURIComponent(state.selectedDate || state.today);
  window.location.href = `/api/export?start_date=${d}&end_date=${d}&format=${fmt}&mode=${mode}`;
}

async function loadStatusAndInitialData() {
  const data = await (await fetch("/api/status")).json();
  state.today = data.today;
  state.selectedDate = data.today;
  state.availableDates = data.available_dates || [data.today];
  updatePauseBadge(data.is_paused);
  $("date-picker").value = state.selectedDate;
  renderDateHistoryPills();
  await Promise.all([loadDailyAnalytics(), loadRawEvents()]);
}

function selectDate(dateStr) {
  state.selectedDate = dateStr;
  state.logOffset = 0;
  $("date-picker").value = dateStr;
  renderDateHistoryPills();
  loadDailyAnalytics();
  loadRawEvents();
}

function renderDateHistoryPills() {
  const wrap = $("date-pills");
  wrap.innerHTML = "";
  for (const d of state.availableDates.slice(0, 7)) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `date-pill ${d === state.selectedDate ? "date-pill-active" : ""}`;
    btn.textContent = d === state.today ? `${d} (Today)` : d;
    btn.addEventListener("click", () => selectDate(d));
    wrap.appendChild(btn);
  }
}

async function loadDailyAnalytics() {
  const report = await (await fetch(`/api/analytics/daily?date=${encodeURIComponent(state.selectedDate)}`)).json();
  state.dailyReport = report;
  renderSummaryKpis(report.summary);
  heatmap.setCounts(report.key_counts, state.selectedKey);
  renderHourlyChart($("hourly-chart"), report.hourly);
  refreshSelectionViews();
}

function handleKeyFilterToggle(keyCode) {
  state.selectedKey = state.selectedKey === keyCode ? "" : keyCode;
  state.logOffset = 0;
  heatmap.setCounts(state.dailyReport?.key_counts || {}, state.selectedKey);
  refreshSelectionViews();
  loadRawEvents();
}

function handleAppFilterToggle(appName) {
  state.selectedApp = state.selectedApp === appName ? "" : appName;
  state.logOffset = 0;
  refreshSelectionViews();
  loadRawEvents();
}

function refreshSelectionViews() {
  if (!state.dailyReport) return;
  renderTopKeysList($("top-keys-list"), state.dailyReport.top_keys, handleKeyFilterToggle, state.selectedKey);
  renderShortcutsList($("top-shortcuts-list"), state.dailyReport.top_shortcuts);
  renderAppsBreakdown($("apps-list"), state.dailyReport.apps, handleAppFilterToggle, state.selectedApp);
  renderDailyKeysTable($("daily-keys-tbody"), state.dailyReport.all_keys, handleKeyFilterToggle, state.selectedKey, state.keySearch);
  const chips = [state.selectedKey && `Key: ${state.selectedKey}`, state.selectedApp && `App: ${state.selectedApp}`].filter(Boolean);
  $("active-filters-label").textContent = chips.length ? `Filtered by ${chips.join(" | ")}` : "Showing all events for selected date";
}

function renderSummaryKpis(s) {
  $("kpi-total").textContent = (s.total_keystrokes || 0).toLocaleString();
  $("kpi-unique").textContent = `${s.unique_keys || 0} unique keys`;
  $("kpi-wpm").textContent = `${s.avg_wpm || 0} WPM`;
  $("kpi-peak-wpm").textContent = `Peak ${s.peak_wpm || 0} WPM`;
  $("kpi-active-time").textContent = formatDuration(s.active_seconds);
  $("kpi-peak-hour").textContent = `Peak hour ${s.peak_hour || "00:00"}`;
  $("kpi-top-key").textContent = s.top_key?.key_label || "-";
  $("kpi-top-key-count").textContent = `${(s.top_key?.count || 0).toLocaleString()} presses`;
  $("kpi-top-app").textContent = s.top_app?.app_name || "-";
  $("kpi-top-app-share").textContent = `${s.top_app?.percentage || 0}% of today`;
}

async function loadRawEvents() {
  const params = new URLSearchParams({
    date: state.selectedDate,
    limit: String(state.logLimit),
    offset: String(state.logOffset),
    key: state.selectedKey,
    app: state.selectedApp,
    search: state.logSearch,
  });
  const data = await (await fetch(`/api/events?${params.toString()}`)).json();
  state.logTotal = data.total || 0;
  renderRawEventsTable($("raw-events-tbody"), data.items);
  const start = state.logTotal === 0 ? 0 : state.logOffset + 1;
  const end = Math.min(state.logOffset + state.logLimit, state.logTotal);
  $("log-page-info").textContent = `${start}-${end} of ${state.logTotal.toLocaleString()}`;
}

function updatePauseBadge(isPaused) {
  state.isPaused = isPaused;
  $("status-dot").className = isPaused ? "status-dot status-paused" : "status-dot status-live";
  $("status-text").textContent = isPaused ? "Paused" : "Recording Live";
  $("btn-toggle-pause").textContent = isPaused ? "Resume Recording" : "Pause Recording";
}

function connectWebSocket() {
  const proto = window.location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${window.location.host}/ws/live`);
  ws.onmessage = (msg) => {
    const payload = JSON.parse(msg.data);
    if (payload.type === "status") updatePauseBadge(payload.is_paused);
    else if (payload.type === "key_event" && payload.event) {
      const ev = payload.event;
      const isViewingToday = state.selectedDate === ev.date_str;
      heatmap.flashKey(ev.key_code, isViewingToday);
      if (isViewingToday) {
        const cur = parseInt($("kpi-total").textContent.replace(/,/g, ""), 10) || 0;
        $("kpi-total").textContent = (cur + 1).toLocaleString();
        if (!state.selectedKey && !state.selectedApp && !state.logSearch && state.logOffset === 0) {
          prependLiveEventRow($("raw-events-tbody"), ev);
          state.logTotal += 1;
        }
      }
    }
  };
  ws.onclose = () => setTimeout(connectWebSocket, 2500);
}

document.addEventListener("DOMContentLoaded", initDashboard);
