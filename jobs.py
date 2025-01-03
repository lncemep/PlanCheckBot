# jobs.py

from database import db_cursor, db_connection

def add_job_record(job_id: str, task_id: int, user_id: int, run_time: str, job_type: str):
    """
    Добавляет запись о job в таблицу jobs.
    run_time — строка вида 'YYYY-MM-DD HH:MM:SS' (UTC).
    """
    db_cursor.execute(
        """
        INSERT INTO jobs (job_id, task_id, user_id, run_time, job_type)
        VALUES (?, ?, ?, ?, ?)
        """,
        (job_id, task_id, user_id, run_time, job_type)
    )
    db_connection.commit()

def remove_job_record(job_id: str):
    """
    Удаляет запись job из таблицы jobs.
    """
    db_cursor.execute(
        "DELETE FROM jobs WHERE job_id = ?",
        (job_id,)
    )
    db_connection.commit()

def get_all_jobs():
    """
    Возвращает все записи job из таблицы jobs.
    """
    db_cursor.execute("SELECT job_id, task_id, user_id, run_time, job_type FROM jobs")
    rows = db_cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "job_id": row[0],
            "task_id": row[1],
            "user_id": row[2],
            "run_time": row[3],
            "job_type": row[4]
        })
    return result