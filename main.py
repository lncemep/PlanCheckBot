# main.py

import logging
from core import dp, bot, router
from handlers import register_handlers
from scheduler import init_scheduler, startup_scheduler

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

    # Запускаем поллинг (создаёт event loop и вызывает on_startup)
    print("[LOG] Запуск polling...")
    dp.run_polling(bot)

if __name__ == "__main__":
    main()