/**
 * metrics.js
 *
 * Мы НЕ трогаем python-логику, поэтому делаем фронт максимально терпимым к формату ответа.
 *
 * Метрики из compare_documents() / evaluator.evaluate():
 * {
 *   ner_precision: 0.9,
 *   ner_recall: 0.8,
 *   ner_f1: 0.85,
 *   tp: 10, fp: 2, fn: 3, support: 13
 * }
 *
 * Возможные дополнительные поля (если бэк решит вернуть):
 * - per_label: { "DIAGNOSIS": { ... }, ... }  (из compare_documents_per_label)
 * - baseline: {...}  (документ baseline)
 * - current: {...}   (документ текущий)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Назад
  const back = document.getElementById("backLink");
  back.addEventListener("click", (e) => {
    e.preventDefault();
    window.history.back();
  });

  // Параметры
  const params = new URLSearchParams(window.location.search);
  const clinReqType = params.get("clinReqType") || localStorage.getItem("clinReqType") || "QUESTIONNARIE";
  const sessionId = params.get("session_id") || null;

  document.getElementById("clinReqTypeLabel").textContent = clinReqType;
  document.getElementById("sessionIdLabel").textContent = sessionId ? sessionId : "не задана";

  const runBtn = document.getElementById("runMetricsBtn");
  runBtn.addEventListener("click", () => runMetrics({ clinReqType, sessionId }));
});

function setStatus(text, kind = "info") {
  const el = document.getElementById("statusText");
  if (!el) return;
  el.textContent = text || "";

  el.style.color =
    kind === "error" ? "#e74c3c" :
    kind === "success" ? "#27ae60" :
    "#334155";
}

function pct(x) {
  const n = Number(x);
  if (!isFinite(n)) return "—";
  return (n * 100).toFixed(1) + "%";
}

function num(x) {
  const n = Number(x);
  if (!isFinite(n)) return "—";
  return String(n);
}

function safeJson(obj) {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
}

/**
 * Пытаемся вытащить метрики из разных обёрток ответа.
 */
function extractMetricsPayload(apiJson) {
  // Самое частое:
  if (apiJson?.metrics && typeof apiJson.metrics === "object") return { metrics: apiJson.metrics, ...apiJson };

  // Иногда: { result: {metrics...}}
  if (apiJson?.result && typeof apiJson.result === "object") {
    const inner = apiJson.result;
    if (inner.metrics) return { metrics: inner.metrics, ...inner };
    if ("ner_f1" in inner || "ner_precision" in inner || "ner_recall" in inner) return { metrics: inner, ...apiJson };
  }

  // Иногда: { evaluation: {...} }
  if (apiJson?.evaluation && typeof apiJson.evaluation === "object") {
    const inner = apiJson.evaluation;
    if (inner.metrics) return { metrics: inner.metrics, ...inner };
    if ("ner_f1" in inner || "ner_precision" in inner || "ner_recall" in inner) return { metrics: inner, ...apiJson };
  }

  // Если сам объект и есть метрики
  if ("ner_f1" in (apiJson || {}) || "ner_precision" in (apiJson || {}) || "ner_recall" in (apiJson || {})) {
    return { metrics: apiJson };
  }

  // Если совсем непонятно — вернём как есть
  return { metrics: null, raw: apiJson };
}

async function runMetrics({ clinReqType, sessionId }) {
  const runBtn = document.getElementById("runMetricsBtn");
  runBtn.disabled = true;
  runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Запуск...';

  // очистка UI
  renderSummary(null);
  renderCounts(null);
  renderPerLabel(null);
  renderDocs(null);

  try {
    setStatus("Запрос к серверу...", "info");

    /**
     * ВАЖНО:
     * Здесь должен быть ТВОЙ реальный эндпоинт.
     *
     * Если у тебя уже есть /api/evaluate-full-pipeline — можешь временно поставить его.
     * Но по твоей текущей python-логике метрик логичнее иметь что-то типа:
     *   POST /api/metrics/evaluate
     * или
     *   POST /api/evaluate-ner
     *
     * Я оставляю универсально: /api/evaluate-ner
     * ЗАМЕНИ на реальный URL твоего бэка.
     */
    const endpoint = "/api/evaluate-ner";

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clinReqType,
        session_id: sessionId, // оставляю snake_case — часто на бэке так
      })
    });

    if (!res.ok) {
      const txt = await res.text().catch(() => "");
      throw new Error(`Ошибка сервера: ${res.status} ${txt}`);
    }

    const apiJson = await res.json();
    const payload = extractMetricsPayload(apiJson);

    if (!payload.metrics) {
      console.error("Не удалось извлечь metrics из ответа:", apiJson);
      throw new Error("Ответ сервера не содержит ожидаемых метрик (ner_f1/ner_precision/ner_recall).");
    }

    setStatus("Готово", "success");

    // Основные метрики
    renderSummary(payload.metrics);

    // TP/FP/FN/support
    renderCounts(payload.metrics);

    // per-label (если бэк отдаёт)
    const perLabel = payload.per_label || payload.perLabel || payload.metrics_per_label || null;
    renderPerLabel(perLabel);

    // baseline/current (если бэк отдаёт)
    const baseline = payload.baseline ?? apiJson.baseline ?? null;
    const current  = payload.current  ?? apiJson.current  ?? null;
    renderDocs({ baseline, current });

  } catch (e) {
    console.error(e);
    setStatus(e.message || "Ошибка", "error");
    alert(e.message || "Ошибка запуска метрик");
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = '<i class="fas fa-play"></i> Запустить метрики';
  }
}

function renderSummary(metrics) {
  const grid = document.getElementById("summaryGrid");
  if (!grid) return;

  if (!metrics) {
    grid.innerHTML = "";
    return;
  }

  grid.innerHTML = `
    <div class="metric-card">
      <div class="metric-title">NER Precision</div>
      <div class="metric-value">${pct(metrics.ner_precision ?? metrics.precision)}</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">NER Recall</div>
      <div class="metric-value">${pct(metrics.ner_recall ?? metrics.recall)}</div>
    </div>
    <div class="metric-card">
      <div class="metric-title">NER F1</div>
      <div class="metric-value">${pct(metrics.ner_f1 ?? metrics.f1)}</div>
    </div>
  `;
}

function renderCounts(metrics) {
  const grid = document.getElementById("countsGrid");
  if (!grid) return;

  if (!metrics) {
    grid.innerHTML = "";
    return;
  }

  grid.innerHTML = `
    <div class="metric-card">
      <div class="metric-title">TP / FP / FN</div>
      <div class="metric-value">
        <span class="pill">TP: ${num(metrics.tp)}</span>
        <span class="pill">FP: ${num(metrics.fp)}</span>
        <span class="pill">FN: ${num(metrics.fn)}</span>
      </div>
    </div>
    <div class="metric-card">
      <div class="metric-title">Support</div>
      <div class="metric-value">${num(metrics.support)}</div>
    </div>
  `;
}

function renderPerLabel(perLabel) {
  const block = document.getElementById("perLabelBlock");
  const tbody = document.getElementById("perLabelTbody");
  if (!block || !tbody) return;

  if (!perLabel || typeof perLabel !== "object" || Array.isArray(perLabel)) {
    block.style.display = "none";
    tbody.innerHTML = "";
    return;
  }

  const rows = Object.entries(perLabel).map(([label, m]) => {
    const p = m.ner_precision ?? m.precision;
