async function api(method, url, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  return { res, json: await res.json().catch(() => null) };
}

function setError(msg) {
  const el = document.getElementById("symbol-error");
  if (el) el.textContent = msg || "";
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("symbol-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      setError("");

      const fd = new FormData(form);
      const payload = {
        symbol: String(fd.get("symbol") || "").trim(),
        exchange: String(fd.get("exchange") || "").trim() || null,
        timezone: String(fd.get("timezone") || "").trim() || null,
      };

      const { res, json } = await api("POST", "/api/symbols", payload);
      if (!res.ok) {
        setError((json && json.detail) || `failed: ${res.status}`);
        return;
      }
      window.location.reload();
    });
  }

  const startBtn = document.getElementById("collector-start");
  if (startBtn) {
    startBtn.addEventListener("click", async () => {
      await api("POST", "/api/collector/start");
      window.location.reload();
    });
  }

  const stopBtn = document.getElementById("collector-stop");
  if (stopBtn) {
    stopBtn.addEventListener("click", async () => {
      await api("POST", "/api/collector/stop");
      window.location.reload();
    });
  }

  document.querySelectorAll(".symbol-delete").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-id");
      if (!id) return;
      await api("DELETE", `/api/symbols/${id}`);
      window.location.reload();
    });
  });
});
