class Questionaries {
  constructor() {
    this.baseUrl = window.location.origin;
  }

  async loadQuestionaries() {
    try {
      const res = await fetch(`${this.baseUrl}/api/questionaries/`);
      if (!res.ok) throw new Error("Ошибка загрузки");

      const data = await res.json();
      const container = document.getElementById("loadQuestionaries");
      container.innerHTML = "";

      data.questions.forEach((q) => {
        const button = document.createElement("button");
        button.className = "btn-card";
        button.innerHTML = `<span>${q.displayName}</span>`;

        button.addEventListener("click", async () => {
          console.log("Выбран опросник:", q.systemName);
          await this.startSession(q.systemName);
        });

        container.appendChild(button);
      });
    } catch (e) {
      const container = document.getElementById("loadQuestionaries");
      container.innerHTML = '<p class="error">Не удалось загрузить список</p>';
      console.error(e);
    }
  }

  async startSession(systemName) {
    localStorage.setItem("clinReqType", systemName);
    window.location.href = `/main-page/${systemName}`;
  }
}

function initRecommendationUploadModal(appInstance) {
  const modal = document.getElementById("uploadModal");
  if (!modal) return;

  const openBtn = document.getElementById("openUploadModal2");

  const form = document.getElementById("uploadForm");
  const fileInput = document.getElementById("pdfFile");
  const fileHint = document.getElementById("fileHint");

  const modalStatus = document.getElementById("modalStatus");
  const headerStatus = document.getElementById("uploadStatus");
  const uploadBtn = document.getElementById("uploadBtn");

  function openModal() {
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    setModalStatus("");
    setHeaderStatus("");
    setTimeout(() => document.getElementById("displayName")?.focus(), 0);
  }

  function closeModal() {
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
  }

  function setModalStatus(text, kind = "info") {
    if (!modalStatus) return;
    modalStatus.textContent = text || "";
    modalStatus.className =
      kind === "success" ? "status--success" :
      kind === "error" ? "status--error" :
      "muted";
  }

  function setHeaderStatus(text, kind = "info") {
    if (!headerStatus) return;
    headerStatus.textContent = text || "";
    headerStatus.className =
      kind === "success" ? "status--success" :
      kind === "error" ? "status--error" :
      "muted";
  }

  openBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    openModal();
  });


  modal.addEventListener("click", (e) => {
    const target = e.target;
    if (target?.dataset?.close === "true") closeModal();
  });

  // закрытие по ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.classList.contains("is-open")) closeModal();
  });

  // подсказка по файлу
  fileInput?.addEventListener("change", () => {
    const f = fileInput.files?.[0];
    if (fileHint) fileHint.textContent = f ? `Выбран: ${f.name}` : "Файл не выбран";
  });

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const displayName = document.getElementById("displayName")?.value?.trim();
    const subtitleName = document.getElementById("subtitleName")?.value?.trim();
    const file = fileInput?.files?.[0];

    if (!displayName || !subtitleName) {
      setModalStatus("Заполните название и системное имя", "error");
      return;
    }
    if (!file) {
      setModalStatus("Выберите PDF файл", "error");
      return;
    }

    if (uploadBtn) {
      uploadBtn.disabled = true;
      uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
    }
    setModalStatus("Загрузка PDF и создание рекомендации...", "info");

    try {
      const fd = new FormData();
      fd.append("file", file);


      const url =
        `/api/parser/?display_name=${encodeURIComponent(displayName)}&subtitle_name=${encodeURIComponent(subtitleName)}`;

      const res = await fetch(url, { method: "POST", body: fd });

      if (!res.ok) {
        const txt = await res.text().catch(() => "");
        throw new Error(`Ошибка сервера: ${res.status} ${txt}`);
      }

      const data = await res.json().catch(() => null);

      setModalStatus("Готово! Рекомендация добавлена.", "success");
      setHeaderStatus("Рекомендация успешно добавлена", "success");


      if (appInstance?.loadQuestionaries) {
        await appInstance.loadQuestionaries();
      }

      form.reset();
      if (fileHint) fileHint.textContent = "Файл не выбран";

      setTimeout(() => closeModal(), 600);

      console.log("Upload response:", data);
    } catch (err) {
      console.error(err);
      setModalStatus(err.message || "Ошибка загрузки", "error");
      setHeaderStatus(err.message || "Ошибка загрузки", "error");
    } finally {
      if (uploadBtn) {
        uploadBtn.disabled = false;
        uploadBtn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Загрузить';
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const app = new Questionaries();
  app.loadQuestionaries();
  initRecommendationUploadModal(app);
});
