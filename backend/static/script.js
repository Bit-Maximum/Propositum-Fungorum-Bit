class QuestionnaireApp {
    constructor() {
        this.sessionId = null;
        this.currentNode = null;
        this.history = [];
        this.baseUrl = window.location.origin;
        this.panZoomInstance = null;


        this.initEventListeners();
        this.updateUI();
    }



    async startNewSession() {
        try {
            let type = localStorage.getItem("clinReqType")
            console.log(type)
            const response = await fetch(`${this.baseUrl}/api/session/start?clinReqType=${type}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error('Не удалось начать сессию');

            const data = await response.json();
            this.sessionId = data.session_id;
            this.currentNode = data.node;
            this.history = [];

            this.hideResult();
            this.updateUI();
            this.loadQuestion(this.currentNode);

        } catch (error) {
            console.error('Ошибка:', error);
            this.showError('Не удалось начать сессию. Пожалуйста, обновите страницу.');
        }
    }

    async submitAnswer() {
        if (!this.sessionId || !this.currentNode) return;

        const answer = this.getCurrentAnswer();
        if (answer === null) {
            this.showError('Пожалуйста, выберите ответ');
            return;
        }

        try {
            const response = await fetch(`${this.baseUrl}/api/session/${this.sessionId}/answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answer: answer })
            });

            if (!response.ok) throw new Error('Ошибка при отправке ответа');

            const data = await response.json();

            // Добавляем в историю
            this.addToHistory(this.currentNode, answer);

            // Обновляем текущий узел
            this.currentNode = data.node;

            if (data.is_final) {
                this.showRecommendation(data);
            } else {
                this.loadQuestion(this.currentNode);
            }

            this.updateUI();

        } catch (error) {
            console.error('Ошибка:', error);
            this.showError('Ошибка при отправке ответа. Попробуйте еще раз.');
        }
    }

    async returnToMainPage() {
        window.location.href = '/';
    }

    async resetSession() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`${this.baseUrl}/api/session/${this.sessionId}/reset`, {
                method: 'POST'
            });

            if (!response.ok) throw new Error('Не удалось сбросить сессию');

            const data = await response.json();
            this.currentNode = data.node;
            this.history = [];

            this.hideResult();
            this.loadQuestion(this.currentNode);
            this.updateUI();

        } catch (error) {
            console.error('Ошибка:', error);
            this.showError('Не удалось сбросить сессию.');
        }
    }



    loadQuestion(node) {
        const questionBody = document.getElementById('questionBody');
        const questionTitle = document.getElementById('questionTitle');
        const questionDescription = document.getElementById('questionDescription');

        // Тексты
        questionTitle.textContent = node.title || 'Вопрос';
        questionDescription.textContent = node.description || 'Пожалуйста, выберите ответ';

        // Очистка
        questionBody.innerHTML = '';

        // Генерация полей ввода
        switch (node.question_type) {
            case 'radio':
                this.createRadioQuestion(node, questionBody);
                break;
            case 'checkbox':
                this.createCheckboxQuestion(node, questionBody);
                break;
            case 'number':
                this.createNumberQuestion(node, questionBody);
                break;
            case 'yesno':
                this.createYesNoQuestion(node, questionBody);
                break;
            default:
                if (node.recommendation) {
                    questionBody.innerHTML = `<div class="recommendation-text">${node.recommendation}</div>`;
                } else if (node.question) {
                    questionBody.innerHTML = `<p>${node.question}</p>`;
                }
        }

        this.updateProgressBar();
    }

    createRadioQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';
        const options = node.options || [];

        options.forEach(option => {
            const label = document.createElement('label');
            label.className = 'option-label';

            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'questionOption';
            input.value = option.value;

            label.appendChild(input);
            label.appendChild(document.createTextNode(option.label));

            // Подсветка выбора
            input.addEventListener('change', () => {
                container.querySelectorAll('.option-label').forEach(l => {
                    l.style.borderColor = 'transparent';
                    l.style.background = '#f8f9fa';
                });
                label.style.borderColor = '#3498db';
                label.style.background = '#e3f2fd';
            });

            form.appendChild(label);
        });
        container.appendChild(form);
    }

    createCheckboxQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';
        const options = node.options || [];

        options.forEach(option => {
            const label = document.createElement('label');
            label.className = 'option-label';

            const input = document.createElement('input');
            input.type = 'checkbox';
            input.name = 'questionOption';
            input.value = option.value;

            label.appendChild(input);
            label.appendChild(document.createTextNode(option.label));
            form.appendChild(label);
        });
        container.appendChild(form);
    }

    createNumberQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';

        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'number-input';
        if (node.validation) {
            if (node.validation.min !== undefined) input.min = node.validation.min;
            if (node.validation.max !== undefined) input.max = node.validation.max;
        }
        input.placeholder = 'Введите значение';

        input.addEventListener('input', () => {
            if (!node.validation) return;

            let value = input.value;
            if (value === '') return;

            value = Number(value);

            if (node.validation.min !== undefined && value < node.validation.min) {
                input.value = node.validation.min;
            }

            if (node.validation.max !== undefined && value > node.validation.max) {
                input.value = node.validation.max;
            }
        });

        form.appendChild(input);
        container.appendChild(form);
        input.focus();
    }

    createYesNoQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';

        const options = [
            { value: true, label: 'Да' },
            { value: false, label: 'Нет' }
        ];

        options.forEach(option => {
            const label = document.createElement('label');
            label.className = 'option-label';

            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'yesNoOption';
            input.value = option.value;

            label.appendChild(input);
            label.appendChild(document.createTextNode(option.label));

            input.addEventListener('change', () => {
                container.querySelectorAll('.option-label').forEach(l => {
                    l.style.borderColor = 'transparent';
                    l.style.background = '#f8f9fa';
                });
                label.style.borderColor = '#3498db';
                label.style.background = '#e3f2fd';
            });

            form.appendChild(label);
        });
        container.appendChild(form);
    }
    prefillAnswer(answer) {
        if (answer === undefined || answer === null || !this.currentNode) return;

        switch (this.currentNode.question_type) {
            case 'radio': {
                const inputs = document.querySelectorAll('input[name="questionOption"]');
                const target = String(answer);
                inputs.forEach(inp => {
                    if (inp.value === target) {
                        inp.checked = true;
                        // чтобы подсветка сработала (у тебя она на change)
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
                break;
            }

            case 'checkbox': {
                if (!Array.isArray(answer)) return;
                const set = new Set(answer.map(String));
                const inputs = document.querySelectorAll('input[name="questionOption"]');
                inputs.forEach(inp => inp.checked = set.has(inp.value));
                break;
            }

            case 'number': {
                const num = document.querySelector('.number-input');
                if (num) num.value = String(answer);
                break;
            }

            case 'yesno': {
                const v = (answer === true || answer === "true") ? "true" : "false";
                const inputs = document.querySelectorAll('input[name="yesNoOption"]');
                inputs.forEach(inp => {
                    if (inp.value === v) {
                        inp.checked = true;
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                });
                break;
            }
        }
    }

    getCurrentAnswer() {
        if (!this.currentNode) return null;

        switch (this.currentNode.question_type) {
            case 'radio':
                const radio = document.querySelector('input[name="questionOption"]:checked');
                return radio ? radio.value : null;
            case 'checkbox':
                const checks = document.querySelectorAll('input[name="questionOption"]:checked');
                return Array.from(checks).map(cb => cb.value);
            case 'number':
                const num = document.querySelector('.number-input');
                return num && num.value !== '' ? parseFloat(num.value) : null;
            case 'yesno':
                const yesno = document.querySelector('input[name="yesNoOption"]:checked');
                return yesno ? (yesno.value === 'true') : null;
            default:
                return null;
        }
    }



    showRecommendation(data) {
        const questionContainer = document.querySelector('.questionnaire-container');
        const resultContainer = document.getElementById('resultContainer');
        const recommendationText = document.getElementById('recommendationText');
        const parametersGrid = document.getElementById('parametersGrid');
        const evidenceLevel = document.getElementById('evidenceLevel');

        recommendationText.textContent = data.recommendation || data.node.recommendation;
        parametersGrid.innerHTML = '';

        const parameters = data.parameters || data.node.parameters || {};

        Object.entries(parameters).forEach(([key, value]) => {
            if (value && typeof value === 'object' && !Array.isArray(value)) {
                // Объект (например, description + options)
                const card = this.createParameterCard(key, value);
                parametersGrid.appendChild(card);
            } else if (Array.isArray(value)) {
                // Список
                const card = document.createElement('div');
                card.className = 'parameter-card';
                card.innerHTML = `
                    <h4><i class="fas fa-list"></i> ${this.formatKey(key)}</h4>
                    <ul>${value.map(item => `<li>${item}</li>`).join('')}</ul>
                `;
                parametersGrid.appendChild(card);
            } else if (value) {
                // Строка/число
                const card = document.createElement('div');
                card.className = 'parameter-card';
                card.innerHTML = `
                    <h4><i class="fas fa-check-circle"></i> ${this.formatKey(key)}</h4>
                    <p>${value}</p>
                `;
                parametersGrid.appendChild(card);
            }
        });

        evidenceLevel.textContent = data.node.evidence_level || 'На основе клинических рекомендаций';

        questionContainer.style.display = 'none';
        resultContainer.style.display = 'block';
    }

    createParameterCard(key, value) {
        const card = document.createElement('div');
        card.className = 'parameter-card';
        let content = `<h4><i class="fas fa-info-circle"></i> ${this.formatKey(key)}</h4>`;

        if (value.description) content += `<p class="param-desc">${value.description}</p>`;

        if (value.options && Array.isArray(value.options)) {
            content += '<ul>';
            value.options.forEach(option => content += `<li>${option}</li>`);
            content += '</ul>';
        }

        card.innerHTML = content;
        return card;
    }

    formatKey(key) {

        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    hideResult() {
        document.querySelector('.questionnaire-container').style.display = 'grid';
        document.getElementById('resultContainer').style.display = 'none';
    }


    addToHistory(node, answer) {
        this.history.unshift({
            node: node,
            answer: answer,
            timestamp: new Date().toLocaleTimeString()
        });
        this.updateHistoryUI();
    }

    updateHistoryUI() {
        const historyList = document.getElementById('historyList');
        if (this.history.length === 0) {
            historyList.innerHTML = `<div class="empty-history"><i class="fas fa-clipboard-list"></i><p>Здесь будет история ответов</p></div>`;
            return;
        }

        historyList.innerHTML = this.history.map(item => `
            <div class="history-item">
                <div class="history-question"><strong>${item.node.title || 'Вопрос'}</strong></div>
                <div class="history-answer">Ответ: ${this.formatAnswer(item.answer)}</div>
                <div class="history-time"><small>${item.timestamp}</small></div>
            </div>
        `).join('');
    }

    formatAnswer(answer) {
        if (Array.isArray(answer)) return answer.join(', ');
        if (typeof answer === 'boolean') return answer ? 'Да' : 'Нет';
        return answer;
    }

    updateProgressBar() {
        const progressBar = document.getElementById('progressBar');
        const progress = this.history.length * 10;
        progressBar.style.width = `${Math.min(progress, 100)}%`;
    }

    updateUI() {
        const sessionInfo = document.getElementById('sessionId');
        const submitButton = document.getElementById('submitButton');
        const backButton = document.getElementById('backButton');

        if (this.sessionId) {
            sessionInfo.textContent = `Сессия: ${this.sessionId.substring(0, 8)}...`;
            sessionInfo.style.color = '#27ae60';
        } else {
            sessionInfo.textContent = 'Сессия: не начата';
            sessionInfo.style.color = '#e74c3c';
        }

        submitButton.disabled = !this.sessionId || !this.currentNode;
        backButton.disabled = this.history.length === 0;

        this.updateHistoryUI();
    }

    async goBack() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`${this.baseUrl}/api/session/${this.sessionId}/back`, {
                method: 'POST'
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || 'Не удалось вернуться назад');
            }

            const data = await response.json();

            // Сервер откатился -> синхронизируем фронт
            this.currentNode = data.node;

            // Локальная история у тебя "новое сверху" (unshift), значит откатываем первый элемент
            if (this.history.length > 0) this.history.shift();

            // Если были результаты — вернёмся к вопросам
            this.hideResult();

            // Рендерим вопрос и (опционально) подставляем прошлый ответ
            this.loadQuestion(this.currentNode);
            this.prefillAnswer(data.prefill_answer);

            this.updateUI();

        } catch (error) {
            console.error('Ошибка goBack:', error);
            this.showError(error.message || 'Не удалось вернуться назад');
        }
    }



    async loadAndRenderGraph() {
        try {
            let type = localStorage.getItem("clinReqType")
            const response = await fetch(`${this.baseUrl}/api/questionnaire/nodes?clinReqType=${type}`);
            if (!response.ok) throw new Error('Ошибка загрузки графа');
            const nodes = await response.json();

            let graphDefinition = 'graph TD\n';

            graphDefinition += 'classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px,font-size:16px;\n';
            graphDefinition += 'classDef start fill:#3498db,color:white,stroke:#2980b9,font-size:18px;\n';
            graphDefinition += 'classDef final fill:#2ecc71,color:white,stroke:#27ae60,font-size:16px;\n';

            nodes.forEach(node => {
                const safeId = node.id;

                let label = (node.title || node.question || node.id);

                label = label.replace(/["'()]/g, "");


                const splitLabel = label.match(/.{1,30}(\s|$)/g);
                if (splitLabel) label = splitLabel.join("<br>");

                if (node.type === 'final') {
                    graphDefinition += `${safeId}("${label}"):::final\n`;
                } else if (node.id === 'Q0') {
                    graphDefinition += `${safeId}(("${label}")):::start\n`;
                } else {
                    graphDefinition += `${safeId}{"${label}"}\n`;
                }

                if (node.transitions) {
                    node.transitions.forEach(trans => {
                        const target = trans.target_node_id;
                        let conditionText = trans.description || trans.condition;
                        conditionText = conditionText.replace(/["'()]/g, "");
                        graphDefinition += `${safeId} --> |"${conditionText}"| ${target}\n`;
                    });
                }
            });

            const graphContainer = document.getElementById('graphContainer');


            if (this.panZoomInstance) {
                this.panZoomInstance.destroy();
                this.panZoomInstance = null;
            }


            graphContainer.innerHTML = graphDefinition;
            graphContainer.removeAttribute('data-processed');
            await mermaid.init(undefined, graphContainer); // Используем await


            const svgElement = graphContainer.querySelector('svg');

            if (svgElement) {

                svgElement.removeAttribute('width');
                svgElement.removeAttribute('height');
                svgElement.removeAttribute('style');
                svgElement.style.width = '100%';
                svgElement.style.height = '100%';
                svgElement.style.maxWidth = 'none';


                this.panZoomInstance = svgPanZoom(svgElement, {
                    zoomEnabled: true,
                    controlIconsEnabled: false,
                    fit: true,
                    center: true,
                    minZoom: 0.1,
                    maxZoom: 50,
                    zoomScaleSensitivity: 0.4,
                    dblClickZoomEnabled: false
                });


                setTimeout(() => {
                    this.panZoomInstance.resize();
                    this.panZoomInstance.fit();
                    this.panZoomInstance.center();
                }, 100);
            }

        } catch (error) {
            console.error('Ошибка отрисовки графа:', error);
            document.getElementById('graphContainer').textContent = 'Не удалось построить граф.';
        }
    }

    // Методы управления модальным окном
    showGraph() {
        const modal = document.getElementById('graphModal');
        modal.style.display = "block";
        this.loadAndRenderGraph();
    }

    closeGraph() {
        const modal = document.getElementById('graphModal');
        modal.style.display = "none";
    }

    // Методы для кнопок ЗУМА
    zoomIn() {
        if (this.panZoomInstance) this.panZoomInstance.zoomIn();
    }

    zoomOut() {
        if (this.panZoomInstance) this.panZoomInstance.zoomOut();
    }

    resetZoomGraph() {
        if (this.panZoomInstance) {
            this.panZoomInstance.resetZoom();
            this.panZoomInstance.resetPan();
            this.panZoomInstance.fit();
            this.panZoomInstance.center();
        }
    }

    downloadRecommendation() {
        const recommendationText = document.getElementById('recommendationText').textContent;
        const parameters = document.getElementById('parametersGrid').innerText;

        const content = `
Клиническая рекомендация
========================
Рекомендация:
${recommendationText}

Детали лечения:
${parameters}

Дата: ${new Date().toLocaleString()}
ID Сессии: ${this.sessionId}
        `;

        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `рекомендация_${this.sessionId.substring(0, 8)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    showError(message) {
        alert(message);
    }

    // Привязка событий
    initEventListeners() {


        window.startNewSession = () => this.startNewSession();
        window.submitAnswer = () => this.submitAnswer();
        window.resetSession = () => this.resetSession();
        window.returnToMainPage = () => this.returnToMainPage();
        window.goBack = () => this.goBack();
        window.printRecommendation = () => window.print();
        window.downloadRecommendation = () => this.downloadRecommendation();

        window.showGraph = () => this.showGraph();
        window.closeGraph = () => this.closeGraph();

        // Кнопки зума
        window.zoomIn = () => this.zoomIn();
        window.zoomOut = () => this.zoomOut();
        window.resetZoomGraph = () => this.resetZoomGraph();

        // Enter для ввода числа
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && this.currentNode?.question_type === 'number') {
                this.submitAnswer();
            }
        });
    }
}


document.addEventListener('DOMContentLoaded', () => {

    mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        flowchart: {
            useMaxWidth: false,
            htmlLabels: true
        }
    });

    window.app = new QuestionnaireApp();

    window.onclick = function(event) {
        const modal = document.getElementById('graphModal');
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});