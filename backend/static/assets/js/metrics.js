document.addEventListener("DOMContentLoaded", () => {
  // Назад
  document.getElementById("backLink").addEventListener("click", (e) => {
    e.preventDefault();
    window.history.back();
  });

  // Файл
  const fileInput = document.getElementById("pdfFile");
  const hint = document.getElementById("fileHint");

  fileInput.addEventListener("change", () => {
    const f = fileInput.files?.[0];
    hint.textContent = f ? `Выбран: ${f.name}` : "Файл не выбран";
  });

  document.getElementById("runMetricsBtn").addEventListener("click", runMetrics);
});

function setStatus(text, kind = "info") {
  const el = document.getElementById("statusText");
  el.textContent = text || "";
  el.style.color =
    kind === "error" ? "#e74c3c" :
    kind === "success" ? "#27ae60" :
    "#334155";
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

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
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
  const fileInput = document.getElementById("pdfFile");
  const file = fileInput.files?.[0];

  clearUI();

  if (!file) {
    setStatus("Сначала выберите PDF файл", "error");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Выполняется...';
  setStatus("Отправка файла на сервер...", "info");

  try {
    const fd = new FormData();
    fd.append("file", file);

    const res = await fetch("/api/parser/metrics", {
      method: "POST",
      body: fd
    });

    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(`Ошибка сервера: ${res.status} ${txt}`);
    }

    const data = await res.json();

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
    alert(e.message || "Ошибка запуска метрик");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-play"></i> Запустить метрики';
  }
}

function renderSummary(m) {
  document.getElementById("summaryGrid").innerHTML = `
    <div class="metric-card">
      <div class="metric-title">NER Precision</div>
      <div class="metric-value">${pct(m.ner_precision)}</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">NER Recall</div>
      <div class="metric-value">${pct(m.ner_recall)}</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">NER F1</div>
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

