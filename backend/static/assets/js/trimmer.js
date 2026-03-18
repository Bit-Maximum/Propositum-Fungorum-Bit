class TrimmerPage {
    constructor() {
        this.baseUrl = window.location.origin;

        this.form = document.getElementById("trimmerForm");
        this.fileInput = document.getElementById("trimFile");
        this.fileHint = document.getElementById("trimFileHint");
        this.submitBtn = document.getElementById("trimSubmitBtn");
        this.resetBtn = document.getElementById("resetBtn");

        this.pageStatus = document.getElementById("pageStatus");
        this.formStatus = document.getElementById("formStatus");

        this.resultCard = document.getElementById("resultCard");
        this.resultMeta = document.getElementById("resultMeta");
        this.resultSummary = document.getElementById("resultSummary");
        this.resultActions = document.getElementById("resultActions");
        this.resultJson = document.getElementById("resultJson");

        this.scrollBtn = document.getElementById("scrollToFormBtn");
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        this.scrollBtn?.addEventListener("click", () => {
            this.form?.scrollIntoView({ behavior: "smooth", block: "start" });
            setTimeout(() => this.fileInput?.focus(), 250);
        });

        this.fileInput?.addEventListener("change", () => {
            const file = this.fileInput.files?.[0];
            this.fileHint.textContent = file ? `Выбран: ${file.name}` : "Файл не выбран";
        });

        this.form?.addEventListener("reset", () => {
            setTimeout(() => {
                this.fileHint.textContent = "Файл не выбран";
                this.setFormStatus("");
                this.setPageStatus("");
                this.hideResult();
            }, 0);
        });

        this.form?.addEventListener("submit", async (e) => {
            e.preventDefault();
            await this.submit();
        });
    }

    setFormStatus(text, kind = "muted") {
        if (!this.formStatus) return;
        this.formStatus.textContent = text || "";
        this.formStatus.className =
            kind === "success"
                ? "status--success"
                : kind === "error"
                    ? "status--error"
                    : kind === "info"
                        ? "status--info"
                        : "muted";
    }

    setPageStatus(text, kind = "muted") {
        if (!this.pageStatus) return;
        this.pageStatus.textContent = text || "";
        this.pageStatus.className =
            kind === "success"
                ? "status--success"
                : kind === "error"
                    ? "status--error"
                    : kind === "info"
                        ? "status--info"
                        : "muted";
    }

    setLoading(isLoading) {
        if (!this.submitBtn) return;

        this.submitBtn.disabled = isLoading;
        if (this.resetBtn) this.resetBtn.disabled = isLoading;

        this.submitBtn.innerHTML = isLoading
            ? '<i class="fas fa-spinner fa-spin"></i> Обработка...'
            : '<i class="fas fa-scissors"></i> Обрезать документ';
    }

    hideResult() {
        if (this.resultCard) this.resultCard.hidden = true;
        if (this.resultSummary) this.resultSummary.innerHTML = "";
        if (this.resultActions) this.resultActions.innerHTML = "";
        if (this.resultJson) this.resultJson.innerHTML = "";
    }

    showResult(data) {
        if (!this.resultCard) return;

        this.resultCard.hidden = false;
        this.resultMeta.textContent = "Успешно обработано";

        const entries = Object.entries(data || {});
        const summaryKeys = [
            "id",
            "file_id",
            "document_id",
            "filename",
            "file_name",
            "pages",
            "page_numbers",
            "page_range",
            "matched_patterns",
            "status"
        ];

        const summaryItems = entries.filter(([key]) => summaryKeys.includes(key));

        if (summaryItems.length > 0) {
            this.resultSummary.innerHTML = summaryItems
                .map(([key, value]) => {
                    const normalizedValue = Array.isArray(value)
                        ? value.join(", ")
                        : typeof value === "object" && value !== null
                            ? JSON.stringify(value)
                            : String(value);

                    return `
            <div class="result-summary__item">
              <span class="result-summary__label">${this.escapeHtml(key)}</span>
              <span class="result-summary__value">${this.escapeHtml(normalizedValue)}</span>
            </div>
          `;
                })
                .join("");
        } else {
            this.resultSummary.innerHTML = `
        <div class="result-summary__item">
          <span class="result-summary__label">Статус</span>
          <span class="result-summary__value">Ответ от сервера получен</span>
        </div>
      `;
        }

        this.renderActionButtons(data);

        this.resultJson.innerHTML = `
      <pre>${this.escapeHtml(JSON.stringify(data, null, 2))}</pre>
    `;

        this.resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    renderActionButtons(data) {
        this.resultActions.innerHTML = "";

        const linkCandidates = [
            data?.download_url,
            data?.file_url,
            data?.result_url,
            data?.url,
            data?.downloadUrl,
        ].filter(Boolean);

        if (linkCandidates.length > 0) {
            linkCandidates.forEach((url, index) => {
                const a = document.createElement("a");
                a.href = url;
                a.className = "btn btn--primary";
                a.target = "_blank";
                a.rel = "noopener noreferrer";
                a.innerHTML = `<i class="fas fa-download"></i> Скачать результат${index ? ` ${index + 1}` : ""}`;
                this.resultActions.appendChild(a);
            });
        }

        const copyBtn = document.createElement("button");
        copyBtn.type = "button";
        copyBtn.className = "btn btn--secondary";
        copyBtn.innerHTML = '<i class="fas fa-copy"></i> Скопировать JSON';
        copyBtn.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
                this.setFormStatus("JSON скопирован в буфер обмена", "success");
            } catch {
                this.setFormStatus("Не удалось скопировать JSON", "error");
            }
        });

        this.resultActions.appendChild(copyBtn);
    }

    async submit() {
        const file = this.fileInput?.files?.[0];

        if (!file) {
            this.setFormStatus("Выберите PDF файл", "error");
            return;
        }

        this.hideResult();
        this.setLoading(true);
        this.setFormStatus("Файл загружается и обрабатывается...", "info");
        this.setPageStatus("Идёт обработка документа", "info");

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch(`${this.baseUrl}/trimmer/`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const errorText = await response.text().catch(() => "");
                throw new Error(`Ошибка сервера: ${response.status} ${errorText}`);
            }

            const data = await response.json();

            this.setFormStatus("Документ успешно обработан", "success");
            this.setPageStatus("Обрезка завершена", "success");
            this.showResult(data);
        } catch (error) {
            console.error(error);
            this.setFormStatus(error.message || "Произошла ошибка при обработке файла", "error");
            this.setPageStatus("Ошибка обработки", "error");
        } finally {
            this.setLoading(false);
        }
    }

    escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const page = new TrimmerPage();
    page.init();
});