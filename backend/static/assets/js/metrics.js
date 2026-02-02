/**
 * Управление страницей метрик
 */
document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('run-full-eval');

    // Переключение видимости шагов (Аккордеон)
    window.toggleStepContent = function(stepId) {
        const content = document.getElementById(`content-${stepId}`);
        content.classList.toggle('open');
    };

    runBtn.addEventListener('click', async () => {
        runBtn.disabled = true;
        runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Выполняется повторный парсинг...';

        try {
            // Запрашиваем у бэкенда полный отчет по всем 4 шагам
            // Бэкенд должен вызвать evaluate_metrics.py и вернуть JSON
            const response = await fetch('/api/evaluate-full-pipeline', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error("Ошибка при получении данных от сервера");

            const data = await response.json();

            // Отрисовываем результаты
            renderStep1(data.step_1);
            renderStep2(data.step_2); // Твой NER отчет
            renderStep3(data.step_3);
            renderStep4(data.step_4);

            // Автоматически открываем Шаг 2, так как он самый важный
            toggleStepContent(2);

        } catch (error) {
            console.error(error);
            alert("Ошибка связи с пайплайном: " + error.message);
        } finally {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="fas fa-play"></i> Запустить полную проверку';
        }
    });
});

/** Рендеринг Шага 1: Структура */
function renderStep1(data) {
    const badge = document.getElementById('badge-1');
    const container = document.getElementById('container-1');

    badge.innerText = (data.metrics.score * 100).toFixed(1) + "%";

    container.innerHTML = `
        <div class="data-box">
            <h4>Baseline Headers</h4>
            ${data.baseline.map(h => `<div>• ${h}</div>`).join('')}
        </div>
        <div class="data-box">
            <h4>Current Headers</h4>
            ${data.current.map(h => `<div>• ${h}</div>`).join('')}
        </div>
    `;
}

/** Рендеринг Шага 2: NER (На основе твоего python-кода) */
function renderStep2(report) {
    const badge = document.getElementById('badge-2');
    const grid = document.getElementById('container-2');
    grid.innerHTML = '';

    let totalF1 = 0;
    let count = 0;

    // Итерируем по объекту, который вернул evaluate_step2 (diagnosis, fixation_type и т.д.)
    for (const [field, data] of Object.entries(report)) {
        totalF1 += data.metrics.f1;
        count++;

        const card = document.createElement('div');
        card.className = 'ner-card';

        const addedHtml = data.metrics.added.map(v => `<span class="ner-tag-added">+ ${v}</span>`).join('');
        const removedHtml = data.metrics.removed.map(v => `<span class="ner-tag-removed">- ${v}</span>`).join('');

        card.innerHTML = `
            <div class="ner-card-header">
                <span style="color: #38bdf8; font-weight:bold; font-size: 0.8rem;">${field.toUpperCase()}</span>
                <span style="font-weight:bold;">${(data.metrics.f1 * 100).toFixed(0)}%</span>
            </div>
            <div>
                ${addedHtml}
                ${removedHtml}
                ${(!addedHtml && !removedHtml) ? '<small style="color:#4b5563">Нет изменений</small>' : ''}
            </div>
        `;
        grid.appendChild(card);
    }

    badge.innerText = (totalF1 / count * 100).toFixed(1) + "%";
}

/** Рендеринг Шага 3: Логика */
function renderStep3(data) {
    const badge = document.getElementById('badge-3');
    const tbody = document.querySelector('#container-3 tbody');
    badge.innerText = (data.total_score * 100).toFixed(1) + "%";

    tbody.innerHTML = data.rules.map(rule => `
        <tr>
            <td><code>${rule.condition}</code></td>
            <td>${rule.target}</td>
            <td>
                <span class="status-pill ${rule.is_match ? 'status-match' : 'status-mismatch'}">
                    ${rule.is_match ? 'MATCH' : 'CHANGED'}
                </span>
            </td>
        </tr>
    `).join('');
}

/** Рендеринг Шага 4: JSON/Graph */
function renderStep4(data) {
    const badge = document.getElementById('badge-4');
    const container = document.getElementById('container-4');

    badge.innerText = data.is_valid ? "OK" : "ERR";
    badge.style.color = data.is_valid ? "#4ade80" : "#f87171";

    container.innerHTML = `
        <div class="data-box">
            <h4>Статистика узлов</h4>
            <div>Узлов (Baseline): ${data.baseline_count}</div>
            <div>Узлов (Current): ${data.current_count}</div>
        </div>
        <div class="data-box">
            <h4>Схема JSON</h4>
            <div style="color: ${data.is_valid ? '#4ade80' : '#f87171'}">
                <i class="fas ${data.is_valid ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                ${data.validation_message || 'Схема валидна'}
            </div>
        </div>
    `;
}