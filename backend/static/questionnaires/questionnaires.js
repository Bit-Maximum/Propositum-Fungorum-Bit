class Questionaries {
    constructor() {
        this.baseUrl = window.location.origin;
    }

    async loadQuestionaries() {
        try {
            const res = await fetch(`${this.baseUrl}/api/questionaries/`);
            if (!res.ok) throw new Error('Ошибка загрузки');

            const data = await res.json();
            const container = document.getElementById('loadQuestionaries');
            container.innerHTML = '';

            data.questions.forEach(q => {
                const button = document.createElement('button');
                button.className = 'btn-card';
                button.innerHTML = `
                    <span>${q.displayName}</span>
                `;

                button.addEventListener('click', async () => {
                    console.log('Выбран опросник:', q.systemName);
                    await this.startSession(q.systemName); // вызываем POST
                });


                container.appendChild(button);
            });

        } catch (e) {
            const container = document.getElementById('loadQuestionaries');
            container.innerHTML = '<p class="error">Не удалось загрузить список</p>';
            console.error(e);
        }
    }

    async startSession(systemName) {
        console.log(systemName)
        window.location.href = `/main-page/${systemName}`
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new Questionaries();
    app.loadQuestionaries();
});
