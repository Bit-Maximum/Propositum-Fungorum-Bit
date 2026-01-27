class QuestionnaireApp {
    constructor() {
        this.sessionId = null;
        this.currentNode = null;
        this.history = [];
        this.baseUrl = window.location.origin;
        
        // Инициализация приложения
        this.initEventListeners();
        this.updateUI();
    }
    
    async startNewSession() {
        try {
            const response = await fetch(`${this.baseUrl}/api/session/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Не удалось начать сессию');
            
            const data = await response.json();
            this.sessionId = data.session_id;
            this.currentNode = data.node;
            this.history = [];
            
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
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    answer: answer
                })
            });
            
            if (!response.ok) throw new Error('Ошибка при отправке ответа');
            
            const data = await response.json();
            
            // Добавляем текущий вопрос в историю
            this.addToHistory(this.currentNode, answer);
            
            // Обновляем состояние
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
        const questionCard = document.getElementById('questionCard');
        const questionBody = document.getElementById('questionBody');
        const questionTitle = document.getElementById('questionTitle');
        const questionDescription = document.getElementById('questionDescription');
        const submitButton = document.getElementById('submitButton');
        const backButton = document.getElementById('backButton');
        
        // Обновляем заголовок и описание
        questionTitle.textContent = node.title || 'Вопрос';
        questionDescription.textContent = node.description || 'Пожалуйста, выберите ответ';
        
        // Очищаем тело вопроса
        questionBody.innerHTML = '';
        
        // В зависимости от типа вопроса создаем соответствующую форму
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
                // Если нет типа вопроса, показываем обычный текст
                if (node.recommendation) {
                    questionBody.innerHTML = `<div class="recommendation-text">${node.recommendation}</div>`;
                } else if (node.question) {
                    questionBody.innerHTML = `<p>${node.question}</p>`;
                }
        }
        
        // Показываем/скрываем кнопки
        submitButton.disabled = false;
        backButton.disabled = this.history.length === 0;
        
        // Обновляем прогресс бар
        this.updateProgressBar();
    }
    
    createRadioQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';
        
        const options = node.options || [];
        const optionGroup = document.createElement('div');
        optionGroup.className = 'option-group';
        
        options.forEach(option => {
            const label = document.createElement('label');
            label.className = 'option-label';
            
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'questionOption';
            input.value = option.value;
            
            label.appendChild(input);
            label.appendChild(document.createTextNode(option.label));
            
            // Добавляем обработчик выбора
            input.addEventListener('change', () => {
                document.querySelectorAll('.option-label').forEach(l => {
                    l.style.borderColor = 'transparent';
                    l.style.background = '#f8f9fa';
                });
                label.style.borderColor = '#3498db';
                label.style.background = '#e3f2fd';
            });
            
            optionGroup.appendChild(label);
        });
        
        form.appendChild(optionGroup);
        container.appendChild(form);
    }
    
    createCheckboxQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';
        
        const options = node.options || [];
        const optionGroup = document.createElement('div');
        optionGroup.className = 'option-group';
        
        options.forEach(option => {
            const label = document.createElement('label');
            label.className = 'option-label';
            
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.name = 'questionOption';
            input.value = option.value;
            
            label.appendChild(input);
            label.appendChild(document.createTextNode(option.label));
            
            optionGroup.appendChild(label);
        });
        
        form.appendChild(optionGroup);
        container.appendChild(form);
    }
    
    createNumberQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';
        
        const input = document.createElement('input');
        input.type = 'number';
        input.className = 'number-input';
        input.min = node.validation?.min || 0;
        input.max = node.validation?.max || 120;
        input.placeholder = 'Введите значение';
        
        form.appendChild(input);
        container.appendChild(form);
    }
    
    createYesNoQuestion(node, container) {
        const form = document.createElement('div');
        form.className = 'question-form';
        
        const optionGroup = document.createElement('div');
        optionGroup.className = 'option-group';
        
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
                document.querySelectorAll('.option-label').forEach(l => {
                    l.style.borderColor = 'transparent';
                    l.style.background = '#f8f9fa';
                });
                label.style.borderColor = '#3498db';
                label.style.background = '#e3f2fd';
            });
            
            optionGroup.appendChild(label);
        });
        
        form.appendChild(optionGroup);
        container.appendChild(form);
    }
    
    getCurrentAnswer() {
        const questionType = this.currentNode?.question_type;
        
        switch (questionType) {
            case 'radio':
                const selectedRadio = document.querySelector('input[name="questionOption"]:checked');
                return selectedRadio ? selectedRadio.value : null;
                
            case 'checkbox':
                const checkboxes = document.querySelectorAll('input[name="questionOption"]:checked');
                return Array.from(checkboxes).map(cb => cb.value);
                
            case 'number':
                const numberInput = document.querySelector('.number-input');
                return numberInput ? parseInt(numberInput.value) : null;
                
            case 'yesno':
                const selectedYesNo = document.querySelector('input[name="yesNoOption"]:checked');
                return selectedYesNo ? selectedYesNo.value === 'true' : null;
                
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
        
        // Заполняем рекомендацию
        recommendationText.textContent = data.recommendation || data.node.recommendation;
        
        // Заполняем параметры
        parametersGrid.innerHTML = '';
        const parameters = data.parameters || data.node.parameters || {};
        
        Object.entries(parameters).forEach(([key, value]) => {
            if (value && typeof value === 'object') {
                // Если параметр - объект (например, с описанием и опциями)
                const card = this.createParameterCard(key, value);
                parametersGrid.appendChild(card);
            } else if (value && Array.isArray(value)) {
                // Если параметр - массив
                const card = document.createElement('div');
                card.className = 'parameter-card';
                card.innerHTML = `
                    <h4><i class="fas fa-list"></i> ${this.formatKey(key)}</h4>
                    <ul>
                        ${value.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                `;
                parametersGrid.appendChild(card);
            } else if (value) {
                // Если параметр - простое значение
                const card = document.createElement('div');
                card.className = 'parameter-card';
                card.innerHTML = `
                    <h4><i class="fas fa-check-circle"></i> ${this.formatKey(key)}</h4>
                    <p>${value}</p>
                `;
                parametersGrid.appendChild(card);
            }
        });
        
        // Уровень доказательности
        evidenceLevel.textContent = data.node.evidence_level || 'На основе клинических рекомендаций';
        
        // Показываем результаты, скрываем вопросы
        questionContainer.style.display = 'none';
        resultContainer.style.display = 'block';
    }
    
    createParameterCard(key, value) {
        const card = document.createElement('div');
        card.className = 'parameter-card';
        
        let content = `<h4><i class="fas fa-info-circle"></i> ${this.formatKey(key)}</h4>`;
        
        if (value.description) {
            content += `<p>${value.description}</p>`;
        }
        
        if (value.options && Array.isArray(value.options)) {
            content += '<ul>';
            value.options.forEach(option => {
                content += `<li>${option}</li>`;
            });
            content += '</ul>';
        }
        
        if (value.advantages && Array.isArray(value.advantages)) {
            content += '<h5>Преимущества:</h5><ul>';
            value.advantages.forEach(adv => {
                content += `<li>${adv}</li>`;
            });
            content += '</ul>';
        }
        
        card.innerHTML = content;
        return card;
    }
    
    formatKey(key) {
        // Преобразуем snake_case в читаемый текст
        return key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase());
    }
    
    hideResult() {
        const questionContainer = document.querySelector('.questionnaire-container');
        const resultContainer = document.getElementById('resultContainer');
        
        questionContainer.style.display = 'grid';
        resultContainer.style.display = 'none';
    }
    
    addToHistory(node, answer) {
        const historyItem = {
            node: node,
            answer: answer,
            timestamp: new Date().toLocaleTimeString()
        };
        
        this.history.unshift(historyItem);
        this.updateHistoryUI();
    }
    
    updateHistoryUI() {
        const historyList = document.getElementById('historyList');
        
        if (this.history.length === 0) {
            historyList.innerHTML = `
                <div class="empty-history">
                    <i class="fas fa-clipboard-list"></i>
                    <p>Здесь будет отображаться история ваших ответов</p>
                </div>
            `;
            return;
        }
        
        historyList.innerHTML = this.history.map(item => `
            <div class="history-item">
                <div class="history-question">
                    <strong>${item.node.title || 'Вопрос'}</strong>
                </div>
                <div class="history-answer">
                    Ответ: ${this.formatAnswer(item.answer)}
                </div>
                <div class="history-time">
                    <small>${item.timestamp}</small>
                </div>
            </div>
        `).join('');
    }
    
    formatAnswer(answer) {
        if (Array.isArray(answer)) {
            return answer.join(', ');
        }
        if (typeof answer === 'boolean') {
            return answer ? 'Да' : 'Нет';
        }
        return answer;
    }
    
    updateProgressBar() {
        const progressBar = document.getElementById('progressBar');
        // Простой расчет прогресса - можно улучшить
        const progress = this.history.length * 10;
        progressBar.style.width = `${Math.min(progress, 100)}%`;
    }
    
    updateUI() {
        const sessionInfo = document.getElementById('sessionId');
        const submitButton = document.getElementById('submitButton');
        const backButton = document.getElementById('backButton');
        
        // Обновляем информацию о сессии
        if (this.sessionId) {
            sessionInfo.textContent = `Сессия: ${this.sessionId.substring(0, 8)}...`;
            sessionInfo.style.color = '#27ae60';
        } else {
            sessionInfo.textContent = 'Сессия: не начата';
            sessionInfo.style.color = '#e74c3c';
        }
        
        // Обновляем состояние кнопок
        submitButton.disabled = !this.sessionId || !this.currentNode;
        backButton.disabled = this.history.length === 0;
        
        // Обновляем историю
        this.updateHistoryUI();
    }
    
    goBack() {
        if (this.history.length > 0) {
            const lastItem = this.history.shift();
            this.currentNode = lastItem.node;
            this.loadQuestion(this.currentNode);
            this.updateUI();
        }
    }
    
    initEventListeners() {
        // Глобальные функции для кнопок HTML
        window.startNewSession = () => this.startNewSession();
        window.submitAnswer = () => this.submitAnswer();
        window.resetSession = () => this.resetSession();
        window.goBack = () => this.goBack();
        window.printRecommendation = () => window.print();
        window.downloadRecommendation = () => this.downloadRecommendation();
        
        // Обработка нажатия Enter для числовых полей
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && this.currentNode?.question_type === 'number') {
                this.submitAnswer();
            }
        });
    }
    
    downloadRecommendation() {
        const recommendationText = document.getElementById('recommendationText').textContent;
        const parameters = document.getElementById('parametersGrid').innerText;
        
        const content = `
Клиническая рекомендация по лечению
====================================

Рекомендация:
${recommendationText}

Параметры лечения:
${parameters}

Сгенерировано: ${new Date().toLocaleString()}
Сессия: ${this.sessionId}
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
        // Простое отображение ошибки - можно заменить на модальное окно
        alert(message);
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.app = new QuestionnaireApp();
});