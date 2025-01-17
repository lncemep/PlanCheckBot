import logging
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from core import dp, bot, router
from handlers import register_handlers
from scheduler import init_scheduler, startup_scheduler
from webapp_server import run_webapp_server

NGROK_URL_PATH = "/home/lncemep/ngrok_url.txt"
NGROK_TIMEOUT = 60  # Время ожидания ссылки (в секундах)


def wait_for_ngrok_url(file_path, timeout=60):
    """
    Ожидание появления URL в ngrok_url.txt
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                url = file.read().strip()
                if url:  # Если файл не пустой
                    print(f"[INFO] ngrok URL найден: {url}")
                    return url
        print("[INFO] Ожидание ngrok URL...")
        time.sleep(5)  # Ждём 5 секунд перед повторной проверкой
    raise TimeoutError(f"[ERROR] Не удалось найти ngrok URL в течение {timeout} секунд.")


async def on_startup():
    """
    Функция, которая вызывается при старте dp.run_polling, 
    когда event loop уже доступен.
    """
    print("[LOG] on_startup: init_scheduler + scheduler.start()")
    # 1) Восстанавливаем job'ы (не вызывая scheduler.start() внутри)
    init_scheduler()
    # 2) Теперь запускаем scheduler
    await startup_scheduler()


def main():
    logging.basicConfig(level=logging.INFO)
    print("[LOG] Запуск main()")

    # Ожидаем URL ngrok перед запуском бота
    try:
        ngrok_url = wait_for_ngrok_url(NGROK_URL_PATH, timeout=NGROK_TIMEOUT)
        print(f"[LOG] Используемый ngrok URL: {ngrok_url}")
    except TimeoutError as e:
        print(str(e))
        return

    # Регистрируем все хендлеры
    register_handlers()
    dp.include_router(router)

    # Регистрируем on_startup-хук 
    dp.startup.register(on_startup)

    # Запускаем HTTP-сервер в отдельном потоке
    server_thread = threading.Thread(target=run_webapp_server, daemon=True)
    server_thread.start()

    # Запускаем поллинг (создаёт event loop и вызывает on_startup)
    print("[LOG] Запуск polling...")
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
