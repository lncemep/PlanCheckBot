console.log("[DEBUG] script.js loaded");

// Считываем "?tg_id=..."
const urlParams = new URLSearchParams(window.location.search);
let userId = parseInt(urlParams.get("tg_id")) || null;

// Глобальные переменные
let userLang = "en";
let userOffset = 0; // UTC offset (int, например +3)
let translations = {};

const statusMsgEl = document.getElementById("status-message");
const tasksContainer = document.getElementById("tasks-container");

// Инициируем всё
init();

async function init() {
  if (!userId) {
    console.error("No userId in URL!");
    statusMsgEl.textContent = "Error: no user_id!";
    return;
  }

  // 1) Грузим user_info
  let info = await fetchUserInfo(userId);
  if (!info) {
    statusMsgEl.textContent = "Ошибка: не могу получить данные о пользователе";
    return;
  }
  userLang = info.language || "en";
  userOffset = info.utc_offset || 0;

  // 2) Грузим переводы
  translations = await fetchTranslations(userLang);
  if (!translations) {
    console.warn("No translations found for lang=", userLang, ", fallback to en");
    translations = {}; // fallback
  }

  // 3) Меняем заголовок <title>
  document.title = translations["title_page"] || "Мои задачи";

  // 4) Загружаем список задач
  await loadTasks();
}

// Запрос к /api/user_info?user_id=...
async function fetchUserInfo(uId) {
  try {
    let resp = await fetch(`/api/user_info?user_id=${uId}`);
    if (!resp.ok) return null;
    let data = await resp.json();
    if (data.error) return null;
    return data;
  } catch (e) {
    console.error(e);
    return null;
  }
}

// Запрос к /api/translations?lang=...
async function fetchTranslations(lang) {
  try {
    let resp = await fetch(`/api/translations?lang=${lang}`);
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    console.error(e);
    return null;
  }
}

/**
 * Загружаем задачи => /api/tasks/<userId>
 */
async function loadTasks() {
  statusMsgEl.textContent = translations["loading_tasks"] || "Loading tasks...";
  tasksContainer.innerHTML = "";

  try {
    let resp = await fetch(`/api/tasks/${userId}`);
    if (!resp.ok) {
      throw new Error("Server error: " + resp.status);
    }
    let tasks = await resp.json();
    if (!tasks || tasks.length === 0) {
      statusMsgEl.textContent = translations["no_tasks"] || "No tasks yet!";
      return;
    }
    statusMsgEl.textContent = "";

    // Сортируем
    tasks.sort((a, b) => {
      let dateA = new Date(a.utc_datetime);
      let dateB = new Date(b.utc_datetime);
      return dateA - dateB;
    });

    tasks.forEach(task => {
      renderTask(task);
    });

  } catch (e) {
    console.error(e);
    statusMsgEl.textContent = translations["error_loading_tasks"] || "Error loading tasks!";
  }
}

/**
 * Рендеринг задачи
 */
function renderTask(task) {
  let card = document.createElement("div");
  card.className = "p-3 bg-white rounded shadow-sm mb-3";

  // Header: title + due_date/time
  let header = document.createElement("div");
  header.className = "d-flex justify-content-between align-items-center mb-2";

  let titleEl = document.createElement("h5");
  titleEl.className = "mb-0";
  titleEl.textContent = task.task_text;

  let timeEl = document.createElement("span");
  timeEl.className = "text-muted small";
  let dueDate = new Date(task.utc_datetime).toLocaleString();
  timeEl.textContent = dueDate;

  header.appendChild(titleEl);
  header.appendChild(timeEl);
  card.appendChild(header);

  // Таймер
  let timerEl = document.createElement("div");
  card.appendChild(timerEl);

  function updateTimer() {
    let now = new Date();
    let due = new Date(task.utc_datetime);
    let diff = due - now;

    if (diff <= 0) {
      timerEl.textContent = translations["deadline_passed"] || "Deadline passed!";
      timerEl.classList.add("text-danger", "fw-bold");
      return;
    }

    let days = Math.floor(diff / (1000 * 60 * 60 * 24));
    let hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
    let minutes = Math.floor((diff / (1000 * 60)) % 60);
    let seconds = Math.floor((diff / 1000) % 60);

    let dStr = days > 0 ? days + (translations["days_suffix"] || "d ") : "";
    let hStr = String(hours).padStart(2, "0");
    let mStr = String(minutes).padStart(2, "0");
    let sStr = String(seconds).padStart(2, "0");

    let txtRemain = translations["remaining"] || "Remaining";
    timerEl.textContent = `${txtRemain}: ${dStr}${hStr}:${mStr}:${sStr}`;
  }

  updateTimer();
  setInterval(updateTimer, 1000);

  // Кнопки
  let btnGroup = document.createElement("div");
  btnGroup.className = "mt-3 d-flex gap-2";

  let completeBtn = document.createElement("button");
  completeBtn.className = "btn btn-success btn-sm";
  completeBtn.textContent = translations["button_complete"] || "Complete";
  completeBtn.onclick = () => updateStatus(task.task_id, "completed");

  let failBtn = document.createElement("button");
  failBtn.className = "btn btn-danger btn-sm";
  failBtn.textContent = translations["button_fail"] || "Fail";
  failBtn.onclick = () => updateStatus(task.task_id, "failed");

  btnGroup.appendChild(completeBtn);
  btnGroup.appendChild(failBtn);
  card.appendChild(btnGroup);

  tasksContainer.appendChild(card);
}

/**
 * Обновление статуса задачи
 */
async function updateStatus(taskId, newStatus) {
  try {
    let resp = await fetch("/api/update_status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId, new_status: newStatus })
    });
    let data = await resp.json();
    if (data.ok) {
      await loadTasks();
    } else {
      alert(translations["update_status_error"] || "Error updating status");
    }
  } catch (e) {
    console.error(e);
    alert(translations["update_status_error"] || "Error updating status");
  }
}
