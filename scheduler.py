# scheduler.py

import logging
from datetime import datetime, timedelta, timezone
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import get_user, increment_statistics, delete_task, db_cursor
from jobs import add_job_record, remove_job_record, get_all_jobs
from core import bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from translations import translations  # <--- чтобы использовать переводы

scheduler = AsyncIOScheduler(timezone=pytz.utc)


async def reminder_job(task_id: int, user_id: int):
    """
    Срабатывает в момент reminder_time. Отправляет пользователю переводимый текст, 
    используя translations["reminder_job_message"].
    """
    db_cursor.execute(
        "SELECT task_text, due_date, due_time FROM tasks WHERE task_id=?",
        (task_id,)
    )
    row = db_cursor.fetchone()
    if not row:
        remove_job_record(f"reminder_{task_id}")
        return

    task_text, due_date, due_time = row

    user = get_user(user_id)
    if not user:
        remove_job_record(f"reminder_{task_id}")
        return

    lang = user.get("language", "ru")  # по умолчанию "ru", если нет

    # Достаём шаблон перевода для напоминания
    reminder_msg_template = translations.get("reminder_job_message", {}).get(
        lang, 
        "🔔Напоминание: скоро задача!\n{task_text}\n(Дата: {due_date}, Время: {due_time})"
    )
    # Подставляем параметры
    msg = reminder_msg_template.format(
        task_text=task_text,
        due_date=due_date,
        due_time=due_time
    )

    try:
        await bot.send_message(chat_id=user_id, text=msg)
    except Exception as e:
        logging.error(f"Failed to send reminder to user_id={user_id}: {e}")

    remove_job_record(f"reminder_{task_id}")


async def due_job(task_id: int, user_id: int):
    """
    Срабатывает в момент due_time: отправляет переводимый текст (translations["due_job_message"])
    + кнопки (button_complete, button_fail). Затем планирует auto_fail.
    """
    db_cursor.execute(
        "SELECT task_text, due_date, due_time FROM tasks WHERE task_id=?",
        (task_id,)
    )
    row = db_cursor.fetchone()
    if not row:
        remove_job_record(f"due_{task_id}")
        return

    task_text, due_date, due_time = row

    user = get_user(user_id)
    if not user:
        remove_job_record(f"due_{task_id}")
        return

    lang = user.get("language", "ru")  # "ru" - fallback

    # Тексты кнопок из переводов
    btn_complete_text = translations.get("button_complete", {}).get(lang, "Выполнено ✅")
    btn_fail_text = translations.get("button_fail", {}).get(lang, "Не выполнено ❌")

    # Создаём InlineKeyboardMarkup правильно (чтобы не было ошибки ValidationError)
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn_complete_text, callback_data=f"complete_{task_id}"),
                InlineKeyboardButton(text=btn_fail_text, callback_data=f"fail_{task_id}")
            ]
        ]
    )

    # Формируем текст через перевод
    due_msg_template = translations.get("due_job_message", {}).get(
        lang,
        (
            "👀Пришло время задачи:\n{task_text}\n"
            "(Дата: {due_date}, Время: {due_time})\n\n"
            "Если не кликнешь за 24ч, всё пропало! 😱"
        )
    )
    msg_text = due_msg_template.format(
        task_text=task_text,
        due_date=due_date,
        due_time=due_time
    )

    try:
        await bot.send_message(chat_id=user_id, text=msg_text, reply_markup=inline_kb)
    except Exception as e:
        logging.error(f"Failed to send due_task to user_id={user_id}: {e}")

    # Удаляем job due_{task_id}
    remove_job_record(f"due_{task_id}")

    # Планируем auto_fail
    auto_fail_time = datetime.utcnow() + timedelta(hours=24)
    auto_fail_job_id = f"auto_fail_{task_id}"
    scheduler.add_job(
        auto_fail_job,
        "date",
        run_date=auto_fail_time,
        args=[task_id, user_id],
        id=auto_fail_job_id,
        replace_existing=True
    )
    add_job_record(
        job_id=auto_fail_job_id,
        task_id=task_id,
        user_id=user_id,
        run_time=auto_fail_time.strftime("%Y-%m-%d %H:%M:%S"),
        job_type="auto_fail"
    )


async def auto_fail_job(task_id: int, user_id: int):
    """
    Если пользователь не нажал кнопки в due_time, через 24 часа 
    помечаем задачу как failed.
    """
    db_cursor.execute(
        "SELECT status FROM tasks WHERE task_id=?",
        (task_id,)
    )
    row = db_cursor.fetchone()
    if not row:
        remove_job_record(f"auto_fail_{task_id}")
        return

    status = row[0]
    if status != "in_process":
        remove_job_record(f"auto_fail_{task_id}")
        return

    increment_statistics(user_id, "failed")
    delete_task(task_id)
    logging.info(f"Task {task_id} auto-failed for user_id={user_id}")
    remove_job_record(f"auto_fail_{task_id}")


def init_scheduler():
    """
    Восстанавливает job'ы из БД (jobs таблица),
    НО НЕ ВЫЗЫВАЕТ scheduler.start() здесь.
    """
    all_jobs = get_all_jobs()
    for job in all_jobs:
        job_id = job["job_id"]
        task_id = job["task_id"]
        user_id = job["user_id"]
        run_time_str = job["run_time"]
        job_type = job["job_type"]

        try:
            dt_utc = datetime.strptime(run_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError as ve:
            logging.error(f"Invalid datetime format for job_id={job_id}: {ve}")
            continue

        if job_type == "reminder":
            scheduler.add_job(
                reminder_job,
                "date",
                run_date=dt_utc,
                args=[task_id, user_id],
                id=job_id,
                replace_existing=True
            )
        elif job_type == "due":
            scheduler.add_job(
                due_job,
                "date",
                run_date=dt_utc,
                args=[task_id, user_id],
                id=job_id,
                replace_existing=True
            )
        elif job_type == "auto_fail":
            scheduler.add_job(
                auto_fail_job,
                "date",
                run_date=dt_utc,
                args=[task_id, user_id],
                id=job_id,
                replace_existing=True
            )
        else:
            logging.warning(f"Unknown job_type={job_type} for job_id={job_id}")

    logging.info("init_scheduler done (no start yet).")


async def startup_scheduler():
    """
    Вызывается при on_startup (main.py),
    когда event loop уже запущен => scheduler.start() безопасен.
    """
    scheduler.start()
    logging.info("Scheduler started inside event loop.")