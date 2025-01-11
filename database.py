# database.py

import sqlite3
from datetime import datetime

# Подключение к базе данных (создаёт файл tasks.db в текущей папке)
db_connection = sqlite3.connect("tasks.db", check_same_thread=False)
db_cursor = db_connection.cursor()

###############################
#    Создание таблиц
###############################

def create_users_table():
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT NOT NULL,
            utc_offset INTEGER NOT NULL DEFAULT 0,
            waiting_for_hour BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db_connection.commit()

def create_tasks_table():
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_text TEXT NOT NULL,
            due_date TEXT NOT NULL,
            due_time TEXT NOT NULL,
            reminder_time TEXT,
            status TEXT DEFAULT 'in_process' CHECK(status IN ('in_process', 'completed', 'failed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
        """
    )
    db_connection.commit()

def create_statistics_table():
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS statistics (
            user_id INTEGER PRIMARY KEY,
            completed_tasks INTEGER DEFAULT 0,
            failed_tasks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
        """
    )
    db_connection.commit()

def create_jobs_table():
    """
    Хранит задания планировщика APScheduler:
    job_id (строка), task_id, user_id, run_time (UTC), job_type
    """
    db_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            task_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            run_time TIMESTAMP NOT NULL,
            job_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
        """
    )
    db_connection.commit()

def initialize_database():
    create_users_table()
    create_tasks_table()
    create_statistics_table()
    create_jobs_table()

###############################
#      Функции для users
###############################

def add_user(user_id: int, language: str = "en", utc_offset: int = 0):
    db_cursor.execute(
        """
        INSERT OR IGNORE INTO users (user_id, language, utc_offset)
        VALUES (?, ?, ?)
        """,
        (user_id, language, utc_offset)
    )
    db_connection.commit()

def update_user_settings(user_id: int, language: str = None, utc_offset: int = None, waiting_for_hour: int = None):
    if language is not None:
        db_cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
    if utc_offset is not None:
        db_cursor.execute("UPDATE users SET utc_offset = ? WHERE user_id = ?", (utc_offset, user_id))
    if waiting_for_hour is not None:
        db_cursor.execute("UPDATE users SET waiting_for_hour = ? WHERE user_id = ?", (waiting_for_hour, user_id))
    db_connection.commit()

def get_user(user_id: int) -> dict:
    db_cursor.execute(
        """
        SELECT user_id, language, utc_offset, waiting_for_hour
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )
    result = db_cursor.fetchone()
    if result:
        return {
            "user_id": result[0],
            "language": result[1],
            "utc_offset": result[2],
            "waiting_for_hour": result[3]
        }
    return None

def set_waiting_for_hour(user_id: int):
    db_cursor.execute(
        """
        UPDATE users
        SET waiting_for_hour = 1
        WHERE user_id = ?
        """,
        (user_id,)
    )
    db_connection.commit()

###############################
#      Функции для tasks
###############################

def add_task(user_id: int, task_text: str, due_date: str, due_time: str, reminder_time: str = None, task_status: str = "in_process"):
    try:
        db_cursor.execute(
            """
            INSERT INTO tasks (user_id, task_text, due_date, due_time, reminder_time, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, task_text, due_date, due_time, reminder_time, task_status)
        )
        db_connection.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Database insertion failed: {e}")
        return False

def get_user_tasks(user_id: int) -> list:
    db_cursor.execute(
        """
        SELECT task_id, task_text, due_date, due_time, status
        FROM tasks
        WHERE user_id = ? AND status = 'in_process'
        ORDER BY due_date, due_time
        """,
        (user_id,)
    )
    return db_cursor.fetchall()

def update_task_status(task_id: int, status: str):
    db_cursor.execute(
        "UPDATE tasks SET status = ? WHERE task_id = ?",
        (status, task_id)
    )
    db_connection.commit()

def delete_task(task_id: int):
    db_cursor.execute(
        "DELETE FROM tasks WHERE task_id = ?",
        (task_id,)
    )
    db_connection.commit()

###############################
#  Функции для statistics
###############################

def increment_statistics(user_id: int, status: str):
    """
    Увеличивает счётчик: 'completed' => completed_tasks, 
                         'failed' => failed_tasks.
    """
    column = "completed_tasks" if status == "completed" else "failed_tasks"
    db_cursor.execute(
        f"""
        INSERT INTO statistics (user_id, {column})
        VALUES (?, 1)
        ON CONFLICT(user_id) DO UPDATE SET {column} = {column} + 1
        """,
        (user_id,)
    )
    db_connection.commit()

def get_user_statistics(user_id: int) -> dict:
    db_cursor.execute(
        """
        SELECT completed_tasks, failed_tasks
        FROM statistics
        WHERE user_id = ?
        """,
        (user_id,)
    )
    result = db_cursor.fetchone()
    if result:
        return {"completed_tasks": result[0], "failed_tasks": result[1]}
    return {"completed_tasks": 0, "failed_tasks": 0}

###############################
#    Отчётные функции
###############################

def get_tasks_due_today(user_id: int, date: str) -> list:
    db_cursor.execute(
        """
        SELECT task_id, task_text, due_time, status
        FROM tasks
        WHERE user_id = ? AND due_date = ? AND status = 'in_process'
        """,
        (user_id, date)
    )
    return db_cursor.fetchall()

def get_weekly_statistics(user_id: int, start_date: str, end_date: str) -> dict:
    db_cursor.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE user_id = ? AND due_date BETWEEN ? AND ? AND status = 'completed'
        """,
        (user_id, start_date, end_date)
    )
    completed = db_cursor.fetchone()[0]

    db_cursor.execute(
        """
        SELECT COUNT(*)
        FROM tasks
        WHERE user_id = ? AND due_date BETWEEN ? AND ? AND status = 'failed'
        """,
        (user_id, start_date, end_date)
    )
    failed = db_cursor.fetchone()[0]

    return {"completed": completed, "failed": failed}

def reset_user_statistics(user_id: int):
    """
    Сбрасывает (обнуляет) статистику пользователя в таблице statistics.
    """
    db_cursor.execute(
        """
        UPDATE statistics
        SET completed_tasks = 0, 
            failed_tasks = 0
        WHERE user_id = ?
        """,
        (user_id,)
    )
    db_connection.commit()


def get_all_users():
    """
    Возвращает список словарей вида [{'user_id': ..., 'language': ...}, ...]
    """
    db_cursor.execute("SELECT user_id, language FROM users")
    rows = db_cursor.fetchall()
    return [{"user_id": row[0], "language": row[1]} for row in rows]

###############################
#   Инициализация при импорте
###############################
initialize_database()