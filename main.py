# main.py

import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from core import dp, bot, router
from handlers import register_handlers
from scheduler import init_scheduler, startup_scheduler

# Определение HTTP-обработчика
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Отвечаем на пинг от UptimeRobot
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"I'm alive!")
        else:
            self.send_response(404)
            self.end_headers()

# Функция для запуска HTTP-сервера
def run_server():
    port = int(os.getenv("PORT", 8080))  # Используем переменную окружения PORT или 8080 по умолчанию
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Starting HTTP server on port {port}")
    httpd.serve_forever()

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

    # Регистрируем все хендлеры
    register_handlers()
    dp.include_router(router)

    # Регистрируем on_startup-хук 
    dp.startup.register(on_startup)

    # Запускаем HTTP-сервер в отдельном потоке
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Запускаем поллинг (создаёт event loop и вызывает on_startup)
    print("[LOG] Запуск polling...")
    dp.run_polling(bot)

if __name__ == "__main__":
    main()