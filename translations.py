# translations.py

translations = {
    "language_selected": {
        "ru": "Вы выбрали Русский язык! 🎉",
        "en": "You have chosen English! 🎉",
        "ua": "Ви обрали Українську мову! 🎉"
    },
    "enter_time_prompt": {
        "ru": "Впиши час (0-23), (например, 15). Это чтоб учесть твой пояс!",
        "ua": "Вкажи годину (0-23), (наприклад, 15). Це потрібно для твого поясу!",
        "en": "Drop the current hour (0-23), (e.g. 15). Helps us set your TZ!"
    },
    "invalid_time_prompt": {
        "ru": "Опа, неверный формат. Час от 0 до 23, окей? ⌚",
        "ua": "Опа, невірний формат. Вкажи годину від 0 до 23, окей? ⌚",
        "en": "Oops, wrong format. Hour from 0 to 23, ok? ⌚"
    },
    "timezone_set": {
        "ru": "Часовой пояс установлен! Разница с UTC: {utc_offset} ч 🔥",
        "ua": "Готово! Різниця з UTC: {utc_offset} год 🔥",
        "en": "Timezone locked! Difference from UTC: {utc_offset} hrs 🔥"
    },
    "settings_buttons": {
        "en": ["🌐Change Language", "⏰Change Timezone"],
        "ru": ["🌐Сменить язык", "⏰Сменить пояс"],
        "ua": ["🌐Змінити мову", "⏰Змінити час"]
    },
    "settings_prompt": {
        "en": "Choose a setting ⚙️:",
        "ru": "Выбери настройку ⚙️:",
        "ua": "Оберіть налаштування ⚙️:"
    },
    "choose_language": {
        "en": "Pick your language 🌏:",
        "ru": "Выбери язык 🌏:",
        "ua": "Оберіть мову 🌏:"
    },
    "select_action": {
        "ru": "Выберите действие 🛠:",
        "en": "Choose an action 🛠:",
        "ua": "Оберіть дію 🛠:"
    },
    "menu": {
        "ru": ("➕ Добавить задачу", "📋 Мои задачи", "📊 Статистика", "⚙️ Настройки"),
        "en": ("➕ Add task", "📋 Show tasks", "📊 Statistics", "⚙️ Settings"),
        "ua": ("➕ Додати завдання", "📋 Мої завдання", "📊 Статистика", "⚙️ Налаштування")
    },
    "day_saved_prompt": {
        "ru": "День зафиксирован 📅",
        "ua": "День збережено 📅",
        "en": "Day saved 📅"
    },
    "unexpected_input": {
        "ru": "Не вкурил... Используйте меню, ок? 🤔",
        "ua": "Не зрозумів... Використай меню, ок? 🤔",
        "en": "Didn't catch that... Use the menu, ok? 🤔"
    },
    "action_cancelled": {
        "ru": "Окей, отменяем и возвращаемся в меню 🚫",
        "ua": "Скасовано, повертаємося в меню 🚫",
        "en": "Cancelled, back to menu 🚫"
    },
    "cancel_button": {
        "ru": "❌Отмена",
        "en": "❌Cancel",
        "ua": "❌Скасувати"
    },
    "add_task_prompt": {
        "ru": "Чё за задачку придумал? Пиши! 📓",
        "en": "What's the task, buddy? 📓",
        "ua": "Яке завдання маєш на думці? Пиши! 📓"
    },
    "select_day_buttons": {
        "ru": ("⏰ Сегодня", "🕒 Завтра", "⌛ Выбрать дату"),
        "en": ("⏰ Today", "🕒 Tomorrow", "⌛ Select date"),
        "ua": ("⏰ Сьогодні", "🕒 Завтра", "⌛ Вибрати дату")
    },
    "select_day_prompt": {
        "ru": "На какой день стряпаем? 📅",
        "en": "Pick a day 📅:",
        "ua": "На який день ставимо завдання? 📅"
    },
    "enter_date_prompt": {
        "ru": "Вбей дату (ДД.ММ.ГГГГ) 📆:",
        "ua": "Введіть дату у форматі ДД.ММ.РРРР 📆:",
        "en": "Enter the date (DD.MM.YYYY) 📆:"
    },
    "invalid_date_prompt": {
        "ru": "Формат даты не тот! ДД.ММ.ГГГГ, чувак ✋",
        "ua": "Формат дати невірний! ДД.ММ.РРРР, друже ✋",
        "en": "Wrong date format! Use DD.MM.YYYY ✋"
    },
    "select_time_prompt": {
        "ru": "Выбирай время для задачи ⏱",
        "en": "Pick a time for the task ⏱",
        "ua": "Обери час для завдання ⏱"
    },
    "custom_time_button": {
        "ru": "Свой вариант 📝",
        "en": "Custom time 📝",
        "ua": "Власний час 📝"
    },
    "enter_custom_time_prompt": {
        "ru": "Формат ЧЧ:ММ, ок? ⌚",
        "en": "Use HH:MM format, ok? ⌚",
        "ua": "Використовуй ГГ:ХХ, ок? ⌚"
    },
    "past_time_error": {
        "ru": "Нельзя в прошлом копать ⏳!",
        "ua": "У минуле не повернемося ⏳!",
        "en": "Can't pick a time that passed ⏳!"
    },
    "time_saved_prompt": {
        "ru": "Записал время! 👍",
        "ua": "Записав час! 👍",
        "en": "Time saved! 👍"
    },
    "no_available_time": {
        "ru": "Свободного времени нет 🙅‍♂️",
        "en": "No free time to pick 🙅‍♂️",
        "ua": "Немає доступного часу для вибору 🙅‍♂️"
    },
    "invalid_option": {
        "ru": "Такой вариант не канает 😬",
        "en": "That option doesn't work 😬",
        "ua": "Такий варіант не підходить 😬"
    },
    "past_date_error": {
        "ru": "Прошлое уходит, нельзя взять! 🔙",
        "en": "Can't choose the past 🔙",
        "ua": "Минуле вже пішло, не обрати! 🔙"
    },
    "task_saved_prompt": {
        "ru": "Текст задачи сохранён. Можешь формить задачу",
        "en": "Task text stored. Proceed to add task",
        "ua": "Текст завдання збережено. Додай саме завдання"
    },
    "select_reminder_time_prompt": {
        "ru": "Когда напомнить? 🔔",
        "ua": "Коли нагадати? 🔔",
        "en": "When to remind you? 🔔"
    },
    "reminder_buttons": {
        "ru": ["⌛ За неделю", "🕒 За час", "⏰ За 10 минут", "❌ Отмена"],
        "ua": ["⌛ За тиждень", "🕒 За годину", "⏰ За 10 хвилин", "❌ Скасувати"],
        "en": ["⌛ In a week", "🕒 In an hour", "⏰ In 10 minutes", "❌ Cancel"]
    },
    "invalid_reminder_time": {
        "ru": "Упс, это время уже прошло 😕",
        "ua": "Упс, цей час вже минув 😕",
        "en": "Oops, that time's gone already 😕"
    },
    "reminder_after_task_error": {
        "ru": "Время напоминания не может быть позже самой задачи!",
        "ua": "Час нагадування не може бути пізнішим за час завдання!",
        "en": "Reminder can't be after the task's own time!"
    },
    "reminder_time_saved": {
        "ru": "Напоминалка активирована 🔔",
        "ua": "Нагадування збережено 🔔",
        "en": "Reminder saved 🔔"
    },
    "enter_custom_reminder_prompt": {
        "ru": "Вбей время для напоминания (ЧЧ:ММ) ⏲️",
        "ua": "Вкажи час нагадування (ГГ:ХХ) ⏲️",
        "en": "Type your reminder time (HH:MM) ⏲️"
    },
    "task_creation_complete": {
        "ru": "Задача создана 🎉",
        "ua": "Завдання створено 🎉",
        "en": "Task created 🎉"
    },
    "task_creation_error": {
        "ru": "Ой, ошибка при создании... 😿",
        "ua": "Помилка під час створення... 😿",
        "en": "Oops, creation error... 😿"
    },
    "task_number": {
        "ru": "Задача №",
        "en": "Task #",
        "ua": "Завдання №"
    },
    "no_active_tasks": {
        "ru": "У вас нет активных задач 🕸",
        "en": "You have no active tasks 🕸",
        "ua": "У вас немає активних завдань 🕸"
    },
    "active_tasks_count": {
        "ru": "🔥Активные задачи",
        "en": "🔥Active Tasks",
        "ua": "🔥Активні завдання"
    },
    "task_text": {
        "ru": "Текст задачи",
        "en": "Task Text",
        "ua": "Текст завдання"
    },
    "due_date": {
        "ru": "Дата выполнения",
        "en": "Due Date",
        "ua": "Дата виконання"
    },
    "due_time": {
        "ru": "Время выполнения",
        "en": "Due Time",
        "ua": "Час виконання"
    },
    "reminder_message": {
        "ru": "🔔Напоминание о задаче: {task_text}\n(Дедлайн: {due_date} {due_time})",
        "en": "🔔Reminder for your task: {task_text}\n(Deadline: {due_date} {due_time})",
        "ua": "🔔Нагадування про завдання: {task_text}\n(Дедлайн: {due_date} {due_time})"
    },
    "task_due_message": {
        "ru": "⏰Задача наступила: {task_text}\n(Дедлайн: {due_date} {due_time})",
        "en": "⏰Your task is due: {task_text}\n(Deadline: {due_date} {due_time})",
        "ua": "⏰Завдання розпочато: {task_text}\n(Дедлайн: {due_date} {due_time})"
    },
    "completed_button": {
        "ru": "Выполнено ✅",
        "en": "Completed ✅",
        "ua": "Виконано ✅"
    },
    "failed_button": {
        "ru": "Не выполнено ❌",
        "en": "Failed ❌",
        "ua": "Не виконано ❌"
    },
    "task_completed_message": {
        "ru": "Задача отмечена как выполненная ✅",
        "en": "Task is marked completed ✅",
        "ua": "Завдання відзначене як виконане ✅"
    },
    "task_failed_message": {
        "ru": "Задача отмечена как проваленная ❌",
        "en": "Task is marked failed ❌",
        "ua": "Завдання відзначене як невиконане ❌"
    },
    "no_tasks": {
        "ru": "Список задач пуст 🫗",
        "en": "Your task list is empty 🫗",
        "ua": "Список завдань порожній 🫗"
    },
    "reminder_job_message": {
        "ru": "🔔Напоминание о задаче: {task_text}\n(Дедлайн: {due_date} {due_time})",
        "en": "🔔Reminder for your task: {task_text}\n(Deadline: {due_date} {due_time})",
        "ua": "🔔Нагадування про завдання: {task_text}\n(Дедлайн: {due_date} {due_time})"
    },
    "due_job_message": {
        "ru": "👀Пришло время задачи:\n{task_text}\n(Дата: {due_date}, Время: {due_time})\n\nЕсли не кликнешь за 24ч, всё пропало! 😱",
        "en": "👀It's task time:\n{task_text}\n(Date: {due_date}, Time: {due_time})\n\nNo click in 24h = fail! 😱",
        "ua": "👀Настав час завдання:\n{task_text}\n(Дата: {due_date}, Час: {due_time})\n\nЯкщо не натиснеш за 24 год, буде провал! 😱"
    },
    "button_complete": {
        "ru": "Готово",
        "en": "Complete",
        "ua": "Готово"
    },
    "button_fail": {
        "ru": "Провал",
        "en": "Fail",
        "ua": "Провал"
    },
        "your_statistics": {
        "ru": "📊 Твоя статистика:",
        "en": "📊 Your Statistics:",
        "ua": "📊 Твоя статистика:"
    },
    "completed": {
        "ru": "Выполнено",
        "en": "Completed",
        "ua": "Виконано"
    },
    "failed": {
        "ru": "Провалено",
        "en": "Failed",
        "ua": "Невиконано"
    },
}