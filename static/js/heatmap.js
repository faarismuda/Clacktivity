/**
 * Interactive Visual Keyboard Heatmap renderer and real-time key flash controller.
 */

import { KEYBOARD_LAYOUTS } from "./layouts.js";

export class KeyboardHeatmap {
  constructor(containerEl, onKeySelect) {
    this.containerEl = containerEl;
    this.onKeySelect = onKeySelect;
    this.currentLayout = "100";
    this.keyCounts = {};
    this.selectedKey = "";
    this.keyElements = new Map();
    this.flashTimers = new Map();
  }

  setLayout(layoutId) {
    if (!KEYBOARD_LAYOUTS[layoutId]) return;
    this.currentLayout = layoutId;
    this.render();
  }

  setCounts(keyCounts, selectedKey = "") {
    this.keyCounts = keyCounts || {};
    this.selectedKey = selectedKey;
    this.render();
  }

  setSelectedKey(keyCode) {
    this.selectedKey = this.selectedKey === keyCode ? "" : keyCode;
    this.updateSelectionStyles();
    if (this.onKeySelect) {
      this.onKeySelect(this.selectedKey);
    }
  }

  computeHeatTier(count, maxCount) {
    if (!count || count <= 0 || maxCount <= 0) return 0;
    const ratio = count / maxCount;
    if (ratio >= 0.75) return 5;
    if (ratio >= 0.45) return 4;
    if (ratio >= 0.20) return 3;
    if (ratio >= 0.06) return 2;
    return 1;
  }

  createKeyButton(keyCode, label, maxCount, extraOpts = {}) {
    const count = this.keyCounts[keyCode] || 0;
    const tier = this.computeHeatTier(count, maxCount);

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `kb-key heat-tier-${tier}`;
    if (this.selectedKey === keyCode) {
      btn.classList.add("kb-key-selected");
    }
    if (extraOpts.widthUnits) {
      btn.style.setProperty("--u", String(extraOpts.widthUnits));
    }
    if (extraOpts.gapBefore && extraOpts.gapBefore > 0) {
      btn.style.setProperty("--gap-before", String(extraOpts.gapBefore));
      btn.classList.add("kb-key-gapped");
    }
    if (extraOpts.gridArea) {
      btn.style.gridRow = extraOpts.gridArea.row;
      btn.style.gridColumn = extraOpts.gridArea.col;
      btn.classList.add("kb-grid-key");
    }

    btn.dataset.keyCode = keyCode;
    btn.title = `${label} (${keyCode}): ${count.toLocaleString()} presses`;

    const legendEl = document.createElement("span");
    legendEl.className = "kb-legend";
    legendEl.textContent = label;

    const countEl = document.createElement("span");
    countEl.className = "kb-count";
    countEl.textContent = count > 0 ? this.formatCompact(count) : "";

    btn.appendChild(legendEl);
    btn.appendChild(countEl);
    btn.addEventListener("click", () => this.setSelectedKey(keyCode));

    this.keyElements.set(keyCode, { btn, countEl, label, isGrid: Boolean(extraOpts.gridArea) });
    return btn;
  }

  renderRowsSection(rows, maxCount, sectionClass) {
    const secEl = document.createElement("div");
    secEl.className = `kb-section ${sectionClass}`;

    rows.forEach((row, rowIdx) => {
      const rowEl = document.createElement("div");
      rowEl.className = rowIdx === 0 && rows.length === 6 ? "kb-row kb-row-fn" : "kb-row";

      for (const item of row) {
        const [keyCode, label, widthUnits = 1, gapBefore = 0] = item;
        const btn = this.createKeyButton(keyCode, label, maxCount, { widthUnits, gapBefore });
        rowEl.appendChild(btn);
      }
      secEl.appendChild(rowEl);
    });
    return secEl;
  }

  renderNumpadSection(numpadItems, maxCount) {
    const padEl = document.createElement("div");
    padEl.className = "kb-numpad-grid";

    // Top-right keyboard status LED strip in row 1
    const leds = document.createElement("div");
    leds.className = "kb-leds";
    leds.innerHTML = `<span>NUM</span><span>CAPS</span><span>SCR</span>`;
    padEl.appendChild(leds);

    for (const nk of numpadItems) {
      const rSpan = nk.rowSpan || 1;
      const cSpan = nk.colSpan || 1;
      const btn = this.createKeyButton(nk.code, nk.label, maxCount, {
        gridArea: {
          row: `${nk.row} / span ${rSpan}`,
          col: `${nk.col} / span ${cSpan}`,
        },
      });
      padEl.appendChild(btn);
    }
    return padEl;
  }

  render() {
    if (!this.containerEl) return;
    const layout = KEYBOARD_LAYOUTS[this.currentLayout] || KEYBOARD_LAYOUTS["100"];
    const counts = Object.values(this.keyCounts);
    const maxCount = counts.length ? Math.max(...counts, 1) : 1;

    this.containerEl.innerHTML = "";
    this.keyElements.clear();

    const boardEl = document.createElement("div");
    boardEl.className = "kb-chassis";

    boardEl.appendChild(this.renderRowsSection(layout.mainRows, maxCount, "kb-main-block"));

    if (layout.navRows) {
      boardEl.appendChild(this.renderRowsSection(layout.navRows, maxCount, "kb-nav-block"));
    }
    if (layout.numpad) {
      boardEl.appendChild(this.renderNumpadSection(layout.numpad, maxCount));
    }

    this.containerEl.appendChild(boardEl);
  }

  updateSelectionStyles() {
    for (const [code, entry] of this.keyElements.entries()) {
      entry.btn.classList.toggle("kb-key-selected", code === this.selectedKey);
    }
  }

  flashKey(keyCode, incrementCount = false) {
    if (incrementCount) {
      this.keyCounts[keyCode] = (this.keyCounts[keyCode] || 0) + 1;
      const counts = Object.values(this.keyCounts);
      const maxCount = counts.length ? Math.max(...counts, 1) : 1;

      for (const [code, entry] of this.keyElements.entries()) {
        const cnt = this.keyCounts[code] || 0;
        const tier = this.computeHeatTier(cnt, maxCount);
        entry.btn.classList.remove("heat-tier-0", "heat-tier-1", "heat-tier-2", "heat-tier-3", "heat-tier-4", "heat-tier-5");
        entry.btn.classList.add(`heat-tier-${tier}`);
        entry.countEl.textContent = cnt > 0 ? this.formatCompact(cnt) : "";
        entry.btn.title = `${entry.label} (${code}): ${cnt.toLocaleString()} presses`;
      }
    }

    const target = this.keyElements.get(keyCode);
    if (!target) return;

    target.btn.classList.add("kb-key-active");
    if (this.flashTimers.has(keyCode)) {
      clearTimeout(this.flashTimers.get(keyCode));
    }
    const timer = setTimeout(() => {
      target.btn.classList.remove("kb-key-active");
      this.flashTimers.delete(keyCode);
    }, 180);
    this.flashTimers.set(keyCode, timer);
  }

  formatCompact(num) {
    if (num >= 10000) return `${(num / 1000).toFixed(1)}k`;
    return String(num);
  }
}
