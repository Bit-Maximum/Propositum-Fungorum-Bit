document.addEventListener("DOMContentLoaded", () => {
  // Назад
  const back = document.getElementById("backLink");
  if (back) {
    back.addEventListener("click", (e) => {
      e.preventDefault();
      window.history.back();
    });
  }

  const runBtn = document.getElementById("runMetricsBtn");
  if (runBtn) runBtn.addEventListener("click", runMetrics);
});

function getUuidFromUrlPath() {
  // ожидаем /metrics/<uuid> (или /metrics/<uuid>/)
  const parts = window.location.pathname.split("/").filter(Boolean);
  const last = parts[parts.length - 1];

  // если вдруг попали на /metrics без uuid
  if (!last || last === "metrics") return null;
  return decodeURIComponent(last);
}

function setStatus(text, kind = "info") {
  const el = document.getElementById("statusText");
  if (!el) return;

  el.textContent = text || "";

  el.classList.remove("status--info", "status--success", "status--error");
  el.classList.add(
    kind === "error" ? "status--error" :
    kind === "success" ? "status--success" :
    "status--info"
  );
}

function pct(x) {
  const n = Number(x);
  return Number.isFinite(n) ? (n * 100).toFixed(1) + "%" : "—";
}

function num(x) {
  const n = Number(x);
  return Number.isFinite(n) ? String(n) : "—";
}

function safeJson(obj) {
  try { return JSON.stringify(obj, null, 2); }
  catch { return String(obj); }
}

function clearUI() {
  document.getElementById("summaryGrid").innerHTML = "";
  document.getElementById("countsRow").innerHTML = "";
  document.getElementById("baselineBox").textContent = "";
  document.getElementById("resultBox").textContent = "";
  document.getElementById("baselinePanel").style.display = "none";
  document.getElementById("resultPanel").style.display = "none";
}

async function runMetrics() {
  const btn = document.getElementById("runMetricsBtn");
  clearUI();

  const uuid = getUuidFromUrlPath();
  if (!uuid) {
    setStatus("Не удалось определить uuid из URL (ожидается /metrics/<uuid>)", "error");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Выполняется...';
  setStatus("Запуск оценки на сервере...", "info");

  try {
    const res = await fetch(`/api/parser/metrics/${encodeURIComponent(uuid)}`, {
      method: "POST",
      headers: { "Accept": "application/json" }
    });

    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(`Ошибка сервера: ${res.status} ${txt}`);
    }

    const data = await res.json();

    // ожидаем { metrics, base?, result? } как раньше
    if (!data.metrics) {
      console.error("Ответ без metrics:", data);
      throw new Error("Сервер не вернул поле metrics");
    }

    renderSummary(data.metrics);
    renderCounts(data.metrics);

    const baselinePanel = document.getElementById("baselinePanel");
    const resultPanel = document.getElementById("resultPanel");

    if (data.base) {
      baselinePanel.style.display = "block";
      document.getElementById("baselineBox").textContent = safeJson(data.base);
    } else {
      baselinePanel.style.display = "none";
    }

    if (data.result) {
      resultPanel.style.display = "block";
      document.getElementById("resultBox").textContent = safeJson(data.result);
    } else {
      resultPanel.style.display = "none";
    }

    setStatus("Готово", "success");

  } catch (e) {
    console.error(e);
    setStatus(e.message || "Ошибка", "error");
    alert(e.message || "Ошибка получения метрик");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-play"></i> Получить метрики';
  }
}

function renderSummary(m) {
  document.getElementById("summaryGrid").innerHTML = `
    <div class="metric-card">
      <div class="metric-label">NER Precision</div>
      <div class="metric-value">${pct(m.ner_precision)}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">NER Recall</div>
      <div class="metric-value">${pct(m.ner_recall)}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">NER F1</div>
      <div class="metric-value">${pct(m.ner_f1)}</div>
    </div>
  `;
}

function renderCounts(m) {
  document.getElementById("countsRow").innerHTML = `
    <div class="counts-grid">
      <div class="count-box">
        <div class="count-label">TP</div>
        <div class="count-value">${num(m.tp)}</div>
      </div>

      <div class="count-box">
        <div class="count-label">FP</div>
        <div class="count-value">${num(m.fp)}</div>
      </div>

      <div class="count-box">
        <div class="count-label">FN</div>
        <div class="count-value">${num(m.fn)}</div>
      </div>

      <div class="count-box">
        <div class="count-label">Support</div>
        <div class="count-value">${num(m.support)}</div>
      </div>
    </div>
  `;
}
