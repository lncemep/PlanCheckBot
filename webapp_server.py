import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

# Импортируем всё нужное из database.py
from database import (
    db_cursor,
    get_user_tasks, 
    update_task_status, 
    get_user_statistics, 
    increment_statistics,
    get_user
)
# Импортируем словарь переводов из отдельного файла
from translations import translations

app = FastAPI(title="Telegram Task WebApp")

# Подключаем папку webapp как статику:
app.mount("/webapp", StaticFiles(directory="webapp"), name="webapp")

###############################
# Модель тела запроса для /api/update_status
###############################
class TaskStatusUpdate(BaseModel):
    task_id: int
    new_status: str

###############################
# Вспомогательная функция: чей task_id?
###############################
def get_task_owner(task_id: int):
    """
    Узнать user_id, которому принадлежит задача.
    Нужно, чтобы дописать статистику, если задача выполнена/провалена.
    """
    db_cursor.execute("SELECT user_id FROM tasks WHERE task_id = ?", (task_id,))
    row = db_cursor.fetchone()
    return row[0] if row else None

###############################
#         Эндпоинты
###############################

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    При заходе на / – редирект на /webapp/index.html
    """
    return """<html>
    <head><meta http-equiv="refresh" content="0; url=/webapp/index.html" /></head>
    <body>Redirecting to /webapp/index.html...</body>
    </html>"""


@app.post("/api/update_status")
async def api_update_status(data: TaskStatusUpdate):
    """
    При клике "Выполнено"/"Провалено" на фронте:
      1) Меняем статус задачи (update_task_status)
      2) Находим user_id задачи -> increment_statistics, если status=completed/failed
    """
    try:
        # (1) Обновляем статус задачи в БД
        update_task_status(data.task_id, data.new_status)

        # (2) Вычисляем user_id, чтобы писать в статистику
        user_id = get_task_owner(data.task_id)
        if not user_id:
            return {"ok": False, "error": "Task owner not found."}

        # Запись в статистику
        if data.new_status in ("completed", "failed"):
            increment_statistics(user_id, data.new_status)

        return {"ok": True, "task_id": data.task_id, "status": data.new_status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/tasks/{user_id}")
async def api_get_tasks(user_id: int):
    """
    Возвращаем список задач для user_id (status='in_process')
    """
    try:
        tasks = get_user_tasks(user_id)
        result = []
        for t in tasks:
            result.append({
                "task_id": t[0],
                "task_text": t[1],
                "due_date": t[2],
                "due_time": t[3],
                "status": t[4],
                "utc_datetime": convert_to_utc(t[2], t[3])  # Добавляем UTC время
            })
        return result
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/stats/{user_id}")
async def user_stats(user_id: int):
    """
    Возвращает { completed, failed } - статистика пользователя
    """
    try:
        stats = get_user_statistics(user_id)  # {"completed_tasks": X, "failed_tasks": Y}
        return {
            "completed": stats["completed_tasks"],
            "failed": stats["failed_tasks"]
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/user_info")
async def api_user_info(user_id: int):
    """
    Возвращаем язык и utc_offset пользователя:
      {
        "user_id": 123,
        "language": "ru",
        "utc_offset": 3,
        ...
      }
    Нужно фронтенду, чтобы правильно считать таймер (и подтянуть переводы).
    """
    try:
        user = get_user(user_id)
        if not user:
            return {"error": "User not found"}

        return {
            "user_id": user["user_id"],
            "language": user["language"],
            "utc_offset": user["utc_offset"]
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/translations")
async def api_translations(lang: str = "ru"):
    """
    Возвращает JSON-словарь переводов для данного языка.
    Если нет ключа, используем английский fallback.
    """
    try:
        result = {}
        for key, subdict in translations.items():
            # subdict - словарь вида { "ru": "...", "en":"...", "ua":"..." }
            result[key] = subdict.get(lang, subdict.get("en", ""))
        return result
    except Exception as e:
        return {"error": str(e)}

###############################
# Вспомогательная функция для преобразования времени в UTC
###############################
def convert_to_utc(due_date: str, due_time: str):
    """
    Преобразует дату и время в UTC datetime.
    """
    try:
        local_time = datetime.strptime(f"{due_date} {due_time}", "%d.%m.%Y %H:%M")
        utc_time = local_time.astimezone(timezone.utc)
        return utc_time.isoformat()
    except Exception as e:
        print(f"[ERROR] Failed to convert time to UTC: {e}")
        return None

###############################
#  Запуск uvicorn
###############################
def run_webapp_server():
    uvicorn.run(app, host="0.0.0.0", port=8080)
