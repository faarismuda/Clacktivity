/**
 * Authentication and Security Modal controller.
 */

const $ = (id) => document.getElementById(id);

let authStatus = { password_enabled: false, authenticated: true, token_expiration_hours: 2 };
let lockCallback = null;

export function handleUnauthorized() {
  const overlay = $("lock-overlay");
  const input = $("lock-password-input");
  const err = $("lock-error");
  if (overlay) overlay.hidden = false;
  if (err) err.textContent = "Session expired. Please enter password.";
  if (input) { input.value = ""; input.focus(); }
  if (lockCallback) lockCallback();
}

export async function initAuth({ onAuthenticated, onLocked }) {
  lockCallback = onLocked;
  const btnSec = $("btn-security");
  const btnLock = $("btn-lock-now");
  const overlay = $("lock-overlay");
  const lockForm = $("lock-form");
  const lockInput = $("lock-password-input");
  const lockErr = $("lock-error");
  const secModal = $("security-modal");
  const secForm = $("security-form");
  const secCurGroup = $("sec-current-password-group");
  const secCurPwd = $("sec-current-password");
  const secNewPwd = $("sec-new-password");
  const secExp = $("sec-expiration-hours");
  const btnDisable = $("btn-disable-password");
  const btnCloseSec = $("btn-close-security");
  const secErr = $("security-error");

  function updateUi() {
    if (btnLock) btnLock.hidden = !authStatus.password_enabled;
    if (btnSec) btnSec.textContent = authStatus.password_enabled ? "Security" : "Set Password";
  }

  try {
    const res = await fetch("/api/auth/status");
    if (res.ok) authStatus = await res.json();
  } catch (_) {}

  updateUi();

  if (authStatus.password_enabled && !authStatus.authenticated) {
    if (overlay) overlay.hidden = false;
    if (lockInput) lockInput.focus();
    if (onLocked) onLocked();
  } else {
    if (overlay) overlay.hidden = true;
    if (onAuthenticated) await onAuthenticated();
  }

  if (lockForm) {
    lockForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (lockErr) lockErr.textContent = "";
      try {
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: lockInput ? lockInput.value : "" }),
        });
        if (res.ok) {
          const data = await res.json();
          authStatus.authenticated = true;
          authStatus.token_expiration_hours = data.token_expiration_hours;
          if (lockInput) lockInput.value = "";
          if (overlay) overlay.hidden = true;
          updateUi();
          if (onAuthenticated) await onAuthenticated();
        } else {
          const err = await res.json().catch(() => ({}));
          if (lockErr) lockErr.textContent = err.detail || "Authentication failed";
        }
      } catch (_) {
        if (lockErr) lockErr.textContent = "Network error. Try again.";
      }
    });
  }

  if (btnLock) {
    btnLock.addEventListener("click", async () => {
      await fetch("/api/auth/logout", { method: "POST" });
      authStatus.authenticated = false;
      if (overlay) overlay.hidden = false;
      if (lockInput) { lockInput.value = ""; lockInput.focus(); }
      if (lockErr) lockErr.textContent = "";
      if (onLocked) onLocked();
    });
  }

  if (btnSec) {
    btnSec.addEventListener("click", () => {
      if (secErr) secErr.textContent = "";
      if (secNewPwd) secNewPwd.value = "";
      if (secCurPwd) secCurPwd.value = "";
      if (secExp) secExp.value = authStatus.token_expiration_hours || 2;
      if (secCurGroup) secCurGroup.hidden = !authStatus.password_enabled;
      if (btnDisable) btnDisable.hidden = !authStatus.password_enabled;
      if (secModal) secModal.hidden = false;
      (authStatus.password_enabled ? secCurPwd : secNewPwd)?.focus();
    });
  }

  if (btnCloseSec) {
    btnCloseSec.addEventListener("click", () => { if (secModal) secModal.hidden = true; });
  }

  if (secForm) {
    secForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (secErr) secErr.textContent = "";
      const payload = {};
      if (authStatus.password_enabled && secCurPwd?.value) payload.current_password = secCurPwd.value;
      if (secNewPwd?.value) payload.new_password = secNewPwd.value;
      if (secExp?.value) payload.token_expiration_hours = parseInt(secExp.value, 10);
      if (!authStatus.password_enabled && !payload.new_password) {
        if (secErr) secErr.textContent = "New password is required";
        return;
      }
      try {
        const res = await fetch("/api/auth/password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json();
          authStatus.password_enabled = data.password_enabled;
          authStatus.authenticated = true;
          authStatus.token_expiration_hours = data.token_expiration_hours;
          updateUi();
          if (secModal) secModal.hidden = true;
        } else {
          const err = await res.json().catch(() => ({}));
          if (secErr) secErr.textContent = err.detail || "Failed to update security settings";
        }
      } catch (_) {
        if (secErr) secErr.textContent = "Network error. Try again.";
      }
    });
  }

  if (btnDisable) {
    btnDisable.addEventListener("click", async () => {
      if (secErr) secErr.textContent = "";
      const payload = { disable: true, current_password: secCurPwd ? secCurPwd.value : "" };
      try {
        const res = await fetch("/api/auth/password", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          authStatus.password_enabled = false;
          authStatus.authenticated = true;
          updateUi();
          if (secModal) secModal.hidden = true;
        } else {
          const err = await res.json().catch(() => ({}));
          if (secErr) secErr.textContent = err.detail || "Failed to disable password";
        }
      } catch (_) {
        if (secErr) secErr.textContent = "Network error. Try again.";
      }
    });
  }
}
