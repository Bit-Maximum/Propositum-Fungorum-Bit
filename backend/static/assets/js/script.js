class QuestionnaireApp {
    constructor() {
        this.sessionId = null;
        this.currentNode = null;
        this.history = [];
        this.baseUrl = window.location.origin;
        this.panZoomInstance = null;

        this.graphNodes = null;
        this.progressModel = null;
        this.progressModelType = null;


        this.initEventListeners();
        this.updateUI();


    }

    async getGraphNodes() {
        const type = localStorage.getItem("clinReqType") || "QUESTIONNARIE";

        if (this.graphNodes && this.progressModelType === type) {
            return this.graphNodes;
        }

        const response = await fetch(`${this.baseUrl}/api/questionnaire/nodes?clinReqType=${type}`);
        if (!response.ok) throw new Error("Не удалось загрузить граф опросника");

        this.graphNodes = await response.json();
        this.progressModelType = type;
        return this.graphNodes;
    }

    buildProgressModel(nodes) {
        const byId = {};
        nodes.forEach(n => { byId[n.id] = n; });

        const memo = {};

        const dfs = (id, stack = new Set()) => {
            if (memo[id]) return memo[id];
            const node = byId[id];

            if (!node) return (memo[id] = { min: 0, max: 0 });
            if (node.type === "final") return (memo[id] = { min: 0, max: 0 });

            if (stack.has(id)) return { min: 1, max: 1 };

            stack.add(id);
            const targets = (node.transitions || [])
                .map(t => t.target_node_id)
                .filter(Boolean);

            if (targets.length === 0) {
                stack.delete(id);
                return (memo[id] = { min: 1, max: 1 });
            }

            const children = targets.map(tid => dfs(tid, new Set(stack)));
            const min = 1 + Math.min(...children.map(c => c.min));
            const max = 1 + Math.max(...children.map(c => c.max));

            stack.delete(id);
            return (memo[id] = { min, max });
        };

        nodes.forEach(n => dfs(n.id));

        return { stepsToFinal: memo };
    }

    async ensureProgressModel() {
        const type = localStorage.getItem("clinReqType") || "QUESTIONNARIE";

        if (this.progressModel && this.progressModelType === type) return;

        const nodes = await this.getGraphNodes();
        this.progressModel = this.buildProgressModel(nodes);
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
            await this.ensureProgressModel();
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

            this.addToHistory(this.currentNode, answer);

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
            await this.ensureProgressModel();
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

        console.log(node);

        questionTitle.textContent = node.title || node.question || 'Вопрос';
        questionDescription.textContent = node.description || 'Пожалуйста, выберите ответ';

        questionBody.innerHTML = '';

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

        input.addEventListener('blur', () => {
            if (!node.validation) return;

            let value = input.value.trim();
            if (value === '') return;

            const numValue = parseFloat(value);

            if (isNaN(numValue)) {
                input.value = '';
                return;
            }

            let correctedValue = numValue;

            value = Number(value);

            if (node.validation.min !== undefined && value < node.validation.min) {
                correctedValue = node.validation.min;
            }

            if (node.validation.max !== undefined && value > node.validation.max) {
                correctedValue = node.validation.max;
            }

            if (correctedValue !== numValue) {
                input.value = correctedValue;
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
        const resultContainer = document.querySelector('.result-container');
        const recommendationText = document.getElementById('recommendationText');
        const parametersGrid = document.getElementById('parametersGrid');
        const evidenceLevel = document.getElementById('evidenceLevel');

        recommendationText.textContent = data.recommendation || data.node.recommendation;
        parametersGrid.innerHTML = '';

        const parameters = data.parameters || data.node.parameters || {};

        Object.entries(parameters).forEach(([key, value]) => {
            if (value && typeof value === 'object' && !Array.isArray(value)) {
                const card = this.createParameterCard(key, value);
                parametersGrid.appendChild(card);
            } else if (Array.isArray(value)) {
                const card = document.createElement('div');
                card.className = 'parameter-card';
                card.innerHTML = `
                    <h4><i class="fas fa-list"></i> ${this.formatKey(key)}</h4>
                    <ul>${value.map(item => `<li>${item}</li>`).join('')}</ul>
                `;
                parametersGrid.appendChild(card);
            } else if (value) {
                const card = document.createElement('div');
                card.className = 'parameter-card';
                card.innerHTML = `
                    <h4><i class="fas fa-check-circle"></i> ${this.formatKey(key)}</h4>
                    <p>${value}</p>
                `;
                parametersGrid.appendChild(card);
            }

            console.log("+");
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
        document.querySelector('.result-container').style.display = 'none';
    }


    addToHistory(node, answer) {
        this.history.unshift({
            node: node,
            answer: answer,
            timestamp: new Date().toLocaleTimeString()
        });
        this.updateHistoryUI();
    }

    getOptionLabel(node, value) {
    if (!node || !node.options) return String(value);

    const target = String(value);
    const opt = node.options.find(o => String(o.value) === target);
    return opt ? opt.label : String(value);
}

formatAnswerForHistory(node, answer) {
    const type = node?.question_type;

    if (type === 'checkbox') {
        if (!Array.isArray(answer)) return String(answer);
        return answer.map(v => this.getOptionLabel(node, v)).join(', ');
    }

    if (type === 'radio') {
        return this.getOptionLabel(node, answer);
    }

    if (type === 'yesno') {
        const v = (answer === true || answer === "true");
        return v ? "Да" : "Нет";
    }

    if (type === 'number') {
        return String(answer);
    }

    try { return JSON.stringify(answer); } catch { return String(answer); }
}

    updateHistoryUI() {
        const historyList = document.getElementById('historyList');
        if (this.history.length === 0) {
            historyList.innerHTML = `<div class="empty-history"><i class="fas fa-clipboard-list"></i>Здесь будет история ответов</div>`;
            return;
        }

        historyList.innerHTML = this.history.map(item => `
            <div class="history-item">
                <div class="history-question"><strong>${item.node.title || 'Вопрос'}</strong></div>
                <div class="history-answer">Ответ: ${this.formatAnswer(item.node, item.answer)}</div>
                <div class="history-time"><small>${item.timestamp}</small></div>
            </div>
        `).join('');
    }

    formatAnswer(node, answer) {
        const qt = node?.question_type;

        if (qt === 'checkbox') {
            if (!Array.isArray(answer)) return String(answer);
            return answer.map(v => this.getOptionLabel(node, v)).join(', ');
        }

        if (qt === 'radio') {
            return this.getOptionLabel(node, answer);
        }

        if (qt === 'yesno' || typeof answer === 'boolean') {
            const v = (answer === true || answer === "true");
            return v ? 'Да' : 'Нет';
        }

        if (qt === 'number') {
            return String(answer);
        }

        if (Array.isArray(answer)) return answer.join(', ');
        return (answer ?? '').toString();
    }

    updateProgressBar() {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        if (!progressBar) return;

        if (!this.currentNode) {
            progressBar.style.width = `0%`;
            if (progressText) progressText.textContent = '';
            return;
        }

        if (!this.progressModel || !this.progressModel.stepsToFinal) {
            const progress = this.history.length * 10;
            progressBar.style.width = `${Math.min(progress, 100)}%`;
            if (progressText) progressText.textContent = '';
            return;
        }

        if (this.currentNode.type === 'final') {
            progressBar.style.width = `100%`;
            if (progressText) progressText.textContent = 'Готово';
            return;
        }

        const answered = this.history.length;
        const currentIndex = answered + 1;

        const dist = this.progressModel.stepsToFinal[this.currentNode.id] || { min: 1, max: 1 };

        const totalMin = answered + dist.min;
        const totalMax = answered + dist.max;
        const totalEst = Math.max(currentIndex, Math.round((totalMin + totalMax) / 2));

        const percent = Math.max(0, Math.min(100, Math.round((currentIndex / totalEst) * 100)));
        progressBar.style.width = `${percent}%`;

        const totalText = (totalMin === totalMax) ? `${totalMin}` : `${totalMin}–${totalMax}`;
        const remMin = Math.max(0, totalMin - currentIndex);
        const remMax = Math.max(0, totalMax - currentIndex);
        const remText = (remMin === remMax) ? `${remMin}` : `${remMin}–${remMax}`;

        if (progressText) {
            progressText.textContent = `Вопрос ${currentIndex} из ${totalText} (осталось ${remText})`;
        }
    }

    updateUI() {
        const sessionInfo = document.getElementById('sessionId');
        const submitButton = document.getElementById('submitButton');
        const backButton = document.getElementById('backButton');

        if (this.sessionId) {
            sessionInfo.textContent = `${this.sessionId.substring(0, 8)}...`;
            sessionInfo.style.color = '#27ae60';
        } else {
            sessionInfo.textContent = 'не начата';
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

            this.currentNode = data.node;

            if (this.history.length > 0) this.history.shift();

            this.hideResult();

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

            graphDefinition += 'classDef default fill:#111827,stroke:#334155,stroke-width:1.5px;\n';
            graphDefinition += 'classDef start fill:#0EA5E9,stroke:#38BDF8,stroke-width:2px;\n';
            graphDefinition += 'classDef final fill:#22C55E,stroke:#4ADE80,stroke-width:2px;\n';
            graphDefinition += 'classDef decision fill:#0B1220,stroke:#64748B,stroke-width:1.5px;\n';


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
                    graphDefinition += `${safeId}{"${label}"}:::decision\n`;
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

    showGraph() {
        const modal = document.getElementById('graphModal');
        modal.style.display = "block";
        this.loadAndRenderGraph();
    }

    closeGraph() {
        const modal = document.getElementById('graphModal');
        modal.style.display = "none";
    }

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

        window.zoomIn = () => this.zoomIn();
        window.zoomOut = () => this.zoomOut();
        window.resetZoomGraph = () => this.resetZoomGraph();

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