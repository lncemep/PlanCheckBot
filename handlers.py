# handlers.py

import re
import asyncio
# import pytz  # можно оставить, если вам нужен pytz где-то ещё, но для localize теперь не используется
from datetime import datetime, time, timedelta, timezone

from aiogram import Bot, Dispatcher, exceptions, types
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from core import bot, dp, router
from config import comands
from translations import translations
from database import (
    db_cursor, 
    add_user,
    update_user_settings,
    get_user,
    add_task,
    set_waiting_for_hour,
    get_user_tasks,
    update_task_status,
    delete_task,
    increment_statistics,
    get_user_statistics,
    get_tasks_due_today,
    get_weekly_statistics
)

from jobs import add_job_record, remove_job_record
from scheduler import scheduler, reminder_job, due_job, init_scheduler

###############################
#   Временное хранилище
###############################
user_tasks = {}

def register_handlers():
    print("[LOG] register_handlers() called. All aiogram handlers are now active.")

###########################
#      Ваши Хендлеры
###########################

user_language = {}

def create_main_menu(lang):
    print(f"[LOG] create_main_menu вызвана для языка: {lang}")
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=translations["menu"][lang][0]), KeyboardButton(text=translations["menu"][lang][1])],
            [KeyboardButton(text=translations["menu"][lang][2]), KeyboardButton(text=translations["menu"][lang][3])]
        ],
        resize_keyboard=True
    )

@router.message(Command(commands=["start"]))
async def start_command(message: Message):
    print(f"[LOG] start_command, text={message.text}")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Український")],
            [KeyboardButton(text="Русский")],
            [KeyboardButton(text="English")]
        ],
        resize_keyboard=True
    )

    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        add_user(user_id=user_id, language="en", utc_offset=0)

    if user_id not in user_tasks:
        user_tasks[user_id] = {}

    await message.reply("Choose a language:", reply_markup=keyboard)


@router.message(lambda message: message.text in ["Український", "Русский", "English"])
async def set_language(message: Message):
    print(f"[LOG] set_language, выбрано: {message.text}")
    lang_map = {"Український": "ua", "Русский": "ru", "English": "en"}
    user_id = message.from_user.id
    lang = lang_map.get(message.text)

    if not lang:
        await message.reply("Error: Unsupported language selected.")
        return

    user = get_user(user_id)
    if not user:
        await message.reply("Error: User not found. Please restart the bot with /start.")
        return

    update_user_settings(user_id=user_id, language=lang)

    await bot.send_message(
        chat_id=message.chat.id,
        text=translations.get("language_selected", {}).get(lang, "Language has been successfully set."),
        reply_markup=ReplyKeyboardRemove()
    )

    if user_tasks.get(user_id, {}).get("waiting_for_language_change"):
        user_tasks[user_id].pop("waiting_for_language_change", None)
        await bot.send_message(
            chat_id=message.chat.id,
            text=translations.get("select_action", {}).get(lang, "Choose an action:"),
            reply_markup=create_main_menu(lang)
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=translations.get("enter_time_prompt", {}).get(lang, "Please enter the current hour (00-23):")
        )
        user_tasks[user_id]["waiting_for_hour"] = True


@router.message(lambda message: get_user(message.from_user.id) and user_tasks.get(message.from_user.id, {}).get("waiting_for_hour"))
async def set_user_hour(message: Message):
    print(f"[LOG] set_user_hour, text={message.text}")
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        await message.answer("Error: User not found. Please restart the bot with /start.")
        return

    lang = user.get("language", "en")

    try:
        user_hour = int(message.text.strip())
        if not (0 <= user_hour <= 23):
            raise ValueError("Invalid hour range")

        server_utc_now = datetime.now(timezone.utc)
        server_utc_hour = server_utc_now.hour

        utc_offset = user_hour - server_utc_hour
        if utc_offset > 12:
            utc_offset -= 24
        elif utc_offset < -12:
            utc_offset += 24

        update_user_settings(user_id=user_id, utc_offset=utc_offset)

        if user_id not in user_tasks:
            user_tasks[user_id] = {}
        user_tasks[user_id]["waiting_for_hour"] = False

        await message.answer(
            translations["timezone_set"].get(lang, "Your timezone has been set. UTC offset: {utc_offset}.").format(utc_offset=utc_offset)
        )
        await message.answer(
            translations["select_action"].get(lang, "Please select an action:"),
            reply_markup=create_main_menu(lang)
        )

    except (ValueError, TypeError):
        await message.answer(
            translations["invalid_time_prompt"].get(lang, "Invalid format. Please enter a number between 0 and 23.")
        )
    except Exception as e:
        print(f"[ERROR] Failed to set user hour for user_id={user_id}: {e}")
        await message.answer("An unexpected error occurred. Please try again later.")


async def send_timezone_confirmation(message: Message, lang: str, utc_offset: int):
    print(f"[LOG] send_timezone_confirmation для user_id={message.from_user.id}, utc_offset={utc_offset}")
    try:
        timezone_set_message = translations["timezone_set"].get(
            lang,
            "Timezone set successfully. UTC offset: {utc_offset}."
        )
        select_action_message = translations["select_action"].get(
            lang,
            "Choose an action:"
        )

        await message.answer(timezone_set_message.format(utc_offset=utc_offset))
        await message.answer(
            select_action_message,
            reply_markup=create_main_menu(lang)
        )

    except KeyError as e:
        print(f"[ERROR] Missing translation for lang={lang}: {e}")
        await message.answer("An error occurred while processing your request. Please try again later.")
    except Exception as e:
        print(f"[ERROR] Failed to send timezone confirmation for user_id={message.from_user.id}: {e}")
        await message.answer("An unexpected error occurred. Please try again.")

@router.message(lambda message: message.text == translations["menu"].get(get_user(message.from_user.id)["language"], [])[2])
async def handle_statistics(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        await message.answer("Пользователь не найден.")
        return
    
    lang = user.get("language", "ru")  # по умолчанию "ru"
    
    # Определяем текст кнопки "Статистика" для текущего языка
    try:
        stats_button_text = translations["menu"][lang][2]
    except (KeyError, IndexError):
        await message.answer("Произошла ошибка при получении статистики.")
        return
    
    # Проверяем, совпадает ли текст сообщения с кнопкой "Статистика"
    if message.text != stats_button_text:
        return
    
    # Получаем статистику пользователя
    stats = get_user_statistics(user_id)
    
    # Формируем сообщение со статистикой
    try:
        stats_message = (
            f"{translations['your_statistics'][lang]}\n"
            f"{translations['completed'][lang]}: {stats['completed_tasks']} ✅\n"
            f"{translations['failed'][lang]}: {stats['failed_tasks']} ❌"
        )
    except KeyError:
        await message.answer("Произошла ошибка при формировании сообщения со статистикой.")
        return
    
    await message.answer(stats_message)

@router.message(lambda message: message.text == translations["menu"].get(get_user(message.from_user.id)["language"], [])[3])
async def settings_menu(message: Message):
    print(f"[LOG] settings_menu, text={message.text}")
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.reply("Error: User not found. Please restart the bot with /start.")
        return

    lang = user.get("language", "en")

    settings_buttons = [
        [KeyboardButton(text=translations["settings_buttons"][lang][0])],
        [KeyboardButton(text=translations["settings_buttons"][lang][1])],
        [KeyboardButton(text=translations["cancel_button"][lang])]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=settings_buttons, resize_keyboard=True)

    await message.reply(
        translations["settings_prompt"][lang],
        reply_markup=keyboard
    )


@router.message(lambda message: message.text in translations["settings_buttons"].get(get_user(message.from_user.id)["language"], []))
async def handle_settings_selection(message: Message):
    print(f"[LOG] handle_settings_selection, text={message.text}")
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.reply("Error: User not found. Please restart the bot with /start.")
        return

    if user_id not in user_tasks:
        user_tasks[user_id] = {}

    lang = user.get("language", "en")

    if message.text == translations["settings_buttons"][lang][0]:
        language_buttons = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Український")],
                [KeyboardButton(text="Русский")],
                [KeyboardButton(text="English")],
                [KeyboardButton(text=translations["cancel_button"][lang])],
            ],
            resize_keyboard=True
        )
        user_tasks[user_id]["waiting_for_language_change"] = True
        await message.reply(
            translations["choose_language"][lang],
            reply_markup=language_buttons
        )

    elif message.text == translations["settings_buttons"][lang][1]:
        await message.reply(
            translations["enter_time_prompt"][lang],
            reply_markup=ReplyKeyboardRemove()
        )
        user_tasks[user_id]["waiting_for_hour"] = True

    elif message.text == translations["cancel_button"][lang]:
        await message.reply(
            translations["action_cancelled"][lang],
            reply_markup=create_main_menu(lang)
        )


@router.message(lambda message: get_user(message.from_user.id) and message.text == translations["menu"][get_user(message.from_user.id)["language"]][0])
async def add_task_button(message: Message):
    print(f"[LOG] add_task_button, text={message.text}")
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        await message.reply("Error: User not found. Please restart the bot with /start.")
        return

    lang = user["language"]
    user_tasks.setdefault(user_id, {})
    user_tasks[user_id]["waiting_for_task_text"] = True

    try:
        task_prompt = translations["add_task_prompt"].get(
            lang, "Please write the task text."
        )
        await bot.send_message(
            chat_id=message.chat.id,
            text=task_prompt,
            reply_markup=ReplyKeyboardRemove()
        )
    except KeyError as e:
        print(f"[ERROR] Missing translation for language {lang}: {e}")
        await message.reply("An error occurred while processing your request. Please try again.")
    except Exception as e:
        print(f"[ERROR] Failed to process 'Add Task' for user_id={user_id}: {e}")
        await message.reply("An unexpected error occurred. Please try again later.")


@router.message(lambda message: user_tasks.get(message.from_user.id, {}).get("waiting_for_task_text"))
async def handle_task_text(message: Message):
    print(f"[LOG] handle_task_text, text={message.text}")
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.reply("Error: User not found. Please restart the bot with /start.")
        return

    lang = user["language"]
    if user_id not in user_tasks:
        user_tasks[user_id] = {}

    user_tasks[user_id].pop("waiting_for_task_text", None)
    task_text = message.text.strip()
    if not task_text:
        await message.reply(
            translations["empty_task_text_error"].get(lang, "Task text cannot be empty.")
        )
        return

    user_tasks[user_id]["text"] = task_text

    try:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=translations["select_day_buttons"][lang][0]),
                    KeyboardButton(text=translations["select_day_buttons"][lang][1])
                ],
                [
                    KeyboardButton(text=translations["cancel_button"][lang]),
                    KeyboardButton(text=translations["select_day_buttons"][lang][2])
                ]
            ],
            resize_keyboard=True
        )
    except KeyError as e:
        print(f"[ERROR] Translation key missing for language '{lang}': {e}")
        await message.reply("An error occurred while creating the keyboard. Please try again.")
        return

    try:
        await bot.send_message(
            chat_id=message.chat.id,
            text=translations["select_day_prompt"].get(lang, "Choose a day for the task."),
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[ERROR] Failed to send message to user {user_id}: {e}")
        await message.reply("An error occurred while sending the message. Please try again.")


@router.message(lambda message: get_user(message.from_user.id) and message.text in [
    translations["select_day_buttons"][get_user(message.from_user.id)["language"]][0],
    translations["select_day_buttons"][get_user(message.from_user.id)["language"]][1],
    translations["select_day_buttons"][get_user(message.from_user.id)["language"]][2],
    translations["cancel_button"][get_user(message.from_user.id)["language"]]
])
async def handle_day_selection(message: Message):
    print(f"[LOG] handle_day_selection, text={message.text}")
    user_id = message.from_user.id
    user = get_user(user_id)

    if not user:
        await message.reply("Error: User not found. Please restart the bot with /start.")
        return

    lang = user["language"]
    timezone_offset = user["utc_offset"]

    if user_id not in user_tasks:
        user_tasks[user_id] = {}

    if message.text == translations["cancel_button"][lang]:
        user_tasks.pop(user_id, None)
        await message.reply(translations["action_cancelled"].get(lang, "Action cancelled."))
        await message.answer(
            translations["select_action"].get(lang, "Choose an action:"),
            reply_markup=create_main_menu(lang)
        )
        return

    if message.text == translations["select_day_buttons"][lang][0]:
        today_date = (datetime.now(timezone.utc) + timedelta(hours=timezone_offset)).strftime("%d.%m.%Y")
        user_tasks[user_id]["day"] = today_date
        await prompt_time_selection(message.chat.id, lang, is_today=True)
        return

    if message.text == translations["select_day_buttons"][lang][1]:
        tomorrow_date = (datetime.now(timezone.utc) + timedelta(hours=timezone_offset, days=1)).strftime("%d.%m.%Y")
        user_tasks[user_id]["day"] = tomorrow_date
        await prompt_time_selection(message.chat.id, lang, is_today=False)
        return

    if message.text == translations["select_day_buttons"][lang][2]:
        user_tasks[user_id]["waiting_for_date"] = True
        await message.reply(
            translations["enter_date_prompt"].get(lang, "Enter the date in the format DD.MM.YYYY:")
        )


@router.message(lambda message: user_tasks.get(message.from_user.id, {}).get("waiting_for_date"))
async def handle_custom_date(message: Message):
    print(f"[LOG] handle_custom_date, text={message.text}")
    user_id = message.from_user.id
    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            return

        lang = user.get("language", "en")
        timezone_offset = user.get("utc_offset", 0)

        selected_date = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset)
        today_date = now.date()

        if selected_date.date() < today_date:
            await message.reply(
                translations["past_date_error"].get(
                    lang, 
                    "You cannot select a past date."
                )
            )
            return

        if user_id not in user_tasks:
            user_tasks[user_id] = {}

        user_tasks[user_id]["day"] = selected_date.strftime("%d.%m.%Y")
        user_tasks[user_id].pop("waiting_for_date", None)

        await prompt_time_selection(message.chat.id, lang, is_today=(selected_date.date() == today_date))

    except ValueError:
        await message.reply(
            translations["invalid_date_prompt"].get(lang, "Invalid date format. Please use DD.MM.YYYY.")
        )
    except KeyError as e:
        print(f"[ERROR] Missing translation for lang={lang}: {e}")
        await message.reply("An error occurred. Please try again.")
    except Exception as e:
        print(f"[ERROR] Unexpected error in handle_custom_date for user {user_id}: {e}")
        await message.reply("An unexpected error occurred while processing the date. Please try again.")


async def prompt_time_selection(chat_id: int, lang: str, is_today: bool):
    print(f"[LOG] prompt_time_selection, chat_id={chat_id}, is_today={is_today}")
    try:
        user = get_user(chat_id)
        if not user:
            await bot.send_message(
                chat_id=chat_id,
                text="Error: User not found. Please restart the bot with /start."
            )
            return

        timezone_offset = user.get("utc_offset", 0)
        now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset)
        current_hour = now.hour if is_today else 0

        time_buttons = [f"{hour:02d}:00" for hour in range(current_hour + 1, 24)]
        if not time_buttons:
            await bot.send_message(
                chat_id=chat_id,
                text=translations["no_available_time"].get(lang, "No available time to select."),
                reply_markup=create_main_menu(lang)
            )
            return

        time_buttons.append(translations["custom_time_button"].get(lang, "Select time"))
        time_buttons.append(translations["cancel_button"].get(lang, "Cancel"))

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=time) for time in time_buttons[i:i + 4]] for i in range(0, len(time_buttons), 4)],
            resize_keyboard=True
        )

        if chat_id not in user_tasks:
            user_tasks[chat_id] = {}
        user_tasks[chat_id]["waiting_for_time"] = True

        await bot.send_message(
            chat_id=chat_id,
            text=translations["select_time_prompt"].get(lang, "Please select a time for the task."),
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"[ERROR] Unexpected error in prompt_time_selection for chat_id={chat_id}: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text="An error occurred while generating time options. Please try again later."
        )


@router.message(lambda message: get_user(message.from_user.id) and message.text == translations["menu"].get(get_user(message.from_user.id)["language"], [])[0])
async def add_task_button_2(message: Message):
    """
    (дубликат) add_task_button - оставляем, если у вас в исходном коде есть дубль
    """
    print(f"[LOG] (дубликат) add_task_button, text={message.text}")
    user_id = message.from_user.id

    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            return

        lang = user.get("language", "en")
        user_tasks.setdefault(user_id, {})

        if user_tasks[user_id].get("waiting_for_task_text"):
            await message.reply(
                translations["task_in_progress"].get(lang, "A task is already being created. Please finish it first.")
            )
            return

        user_tasks[user_id]["waiting_for_task_text"] = True

        await bot.send_message(
            chat_id=message.chat.id,
            text=translations["add_task_prompt"].get(lang, "Please enter the task text."),
            reply_markup=ReplyKeyboardRemove()
        )

    except KeyError as e:
        print(f"[ERROR] Translation error for user {user_id}: {e}")
        await message.reply("A translation error occurred. Please try again later.")
    except Exception as e:
        print(f"[ERROR] Error in add_task_button for user {user_id}: {e}")
        await message.reply("An unexpected error occurred. Please try again later.")


@router.message(lambda message: user_tasks.get(message.from_user.id, {}).get("waiting_for_task_text"))
async def handle_task_text_2(message: Message):
    """
    (дубликат) handle_task_text
    """
    print(f"[LOG] (дубликат) handle_task_text, text={message.text}")
    user_id = message.from_user.id

    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            return

        lang = user.get("language", "en")

        task_text = message.text.strip()
        if not task_text:
            await message.reply(translations["empty_task_text_error"].get(lang, "Task text cannot be empty."))
            return

        if len(task_text) > 500:
            await message.reply(translations["task_text_too_long"].get(lang, "The task text is too long."))
            return

        user_tasks.setdefault(user_id, {})
        user_tasks[user_id]["text"] = task_text
        user_tasks[user_id]["waiting_for_task_text"] = False

        try:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text=translations["select_day_buttons"][lang][0]),
                        KeyboardButton(text=translations["select_day_buttons"][lang][1])
                    ],
                    [
                        KeyboardButton(text=translations["cancel_button"][lang]),
                        KeyboardButton(text=translations["select_day_buttons"][lang][2])
                    ]
                ],
                resize_keyboard=True
            )
        except KeyError as ke:
            print(f"[ERROR] Translation key missing for language {lang}: {ke}")
            await message.reply("Error occurred while creating the selection menu. Please try again later.")
            return

        await bot.send_message(
            chat_id=message.chat.id,
            text=translations["select_day_prompt"].get(lang, "Please select a day."),
            reply_markup=keyboard
        )

    except KeyError as ke:
        print(f"[ERROR] KeyError in handle_task_text: {ke}")
        await message.reply("An error occurred with language configuration. Please try again later.")
    except Exception as e:
        print(f"[ERROR] Error in handle_task_text for user {user_id}: {e}")
        await message.reply("An unexpected error occurred. Please try again later.")


@router.message(lambda message: user_tasks.get(message.from_user.id, {}).get("waiting_for_date"))
async def handle_custom_date_2(message: Message):
    """
    (дубликат) handle_custom_date
    """
    print(f"[LOG] (дубликат) handle_custom_date, text={message.text}")
    user_id = message.from_user.id

    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            return

        lang = user["language"]
        timezone_offset = user.get("utc_offset", 0)

        try:
            selected_date = datetime.strptime(message.text.strip(), "%d.%m.%Y")
        except ValueError:
            await message.reply(translations["invalid_date_prompt"].get(
                lang, "Invalid date format. Please use DD.MM.YYYY."
            ))
            return

        now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset)
        today_date = now.date()

        if selected_date.date() < today_date:
            await message.reply(translations["past_date_error"].get(
                lang, "You cannot select a past date."
            ))
            return

        user_tasks.setdefault(user_id, {})["day"] = selected_date.strftime("%d.%m.%Y")
        user_tasks[user_id].pop("waiting_for_date", None)

        await prompt_time_selection(message.chat.id, lang, is_today=(selected_date.date() == today_date))

    except KeyError as ke:
        print(f"[ERROR] KeyError in handle_custom_date: {ke}")
        await message.reply("An error occurred with language configuration. Please try again later.")
    except Exception as e:
        print(f"[ERROR] Error in handle_custom_date: {e}")
        await message.reply("An unexpected error occurred while processing the date. Please try again.")


@router.message(lambda message: user_tasks.get(message.from_user.id, {}).get("waiting_for_time"))
async def handle_time_selection(message: Message):
    print(f"[LOG] handle_time_selection, text={message.text}")
    user_id = message.from_user.id
    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            return

        lang = user.get("language", "en")
        timezone_offset = user.get("utc_offset", 0)

        if message.text == translations.get("cancel_button", {}).get(lang, "Cancel"):
            user_tasks.pop(user_id, None)
            await message.reply(
                translations.get("action_cancelled", {}).get(lang, "Action cancelled.")
            )
            await message.answer(
                translations.get("select_action", {}).get(lang, "Choose an action:"),
                reply_markup=create_main_menu(lang)
            )
            return

        if message.text == translations.get("custom_time_button", {}).get(lang, "Custom time"):
            user_tasks[user_id].pop("waiting_for_time", None)
            user_tasks[user_id]["waiting_for_custom_time"] = True

            await message.reply(
                translations.get("enter_custom_time_prompt", {}).get(lang, "Enter the time in HH:MM format."),
                reply_markup=ReplyKeyboardRemove()
            )
            return

        try:
            selected_time = datetime.strptime(message.text.strip(), "%H:%M").time()
        except ValueError:
            await message.reply(
                translations.get("invalid_time_prompt", {}).get(lang, "Invalid time format. Please use HH:MM.")
            )
            return

        now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=timezone_offset)))

        if "day" not in user_tasks.get(user_id, {}):
            await message.reply(
                translations.get("task_date_missing", {}).get(lang, "Task date is missing. Please restart the process.")
            )
            return

        selected_day = datetime.strptime(user_tasks[user_id]["day"], "%d.%m.%Y").date()
        is_today = selected_day == now.date()
        if is_today and selected_time <= now.time():
            await message.reply(
                translations.get("past_time_error", {}).get(lang, "You cannot select a time earlier than now.")
            )
            return

        user_tasks[user_id]["time"] = message.text.strip()
        user_tasks[user_id].pop("waiting_for_time", None)

        await message.reply(
            f"{translations.get('time_saved_prompt', {}).get(lang, 'Time saved')}: {message.text.strip()}"
        )

        await prompt_reminder_time(message.chat.id, lang)

    except KeyError as ke:
        print(f"[ERROR] KeyError in handle_time_selection: {ke}")
        await message.reply("An error occurred with translations. Please try again later.")
    except Exception as e:
        print(f"[ERROR] Error in handle_time_selection: {e}")
        await message.reply("An unexpected error occurred. Please try again later.")


@router.message(lambda message: user_tasks.get(message.from_user.id, {}).get("waiting_for_custom_time"))
async def handle_custom_time_input(message: Message):
    print(f"[LOG] handle_custom_time_input, text={message.text}")
    user_id = message.from_user.id

    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            return

        lang = user.get("language", "en")
        timezone_offset = user.get("utc_offset", 0)

        corrected_text = message.text.strip()
        corrected_text = re.sub(r"[：﹕∶꞉︓]", ":", corrected_text)

        if "day" not in user_tasks.get(user_id, {}):
            await message.reply(
                translations.get("task_date_missing", {}).get(lang, "Task date is missing. Please restart the process.")
            )
            return

        try:
            selected_time = datetime.strptime(corrected_text, "%H:%M").time()
        except ValueError:
            await message.reply(
                translations.get("invalid_time_prompt", {}).get(lang, "Invalid time format. Please use HH:MM.")
            )
            return

        now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=timezone_offset)))
        selected_day = datetime.strptime(user_tasks[user_id]["day"], "%d.%m.%Y").date()
        is_today = selected_day == now.date()
        if is_today and selected_time <= now.time():
            await message.reply(
                translations.get("past_time_error", {}).get(lang, "You cannot select a time earlier than now.")
            )
            return

        user_tasks[user_id]["time"] = corrected_text
        user_tasks[user_id].pop("waiting_for_custom_time", None)

        await message.reply(
            f"{translations.get('time_saved_prompt', {}).get(lang, 'Time saved')}: {corrected_text}"
        )

        await prompt_reminder_time(message.chat.id, lang)

    except KeyError as ke:
        print(f"[ERROR] KeyError in handle_custom_time_input: {ke}")
        await message.reply("An error occurred with translations. Please try again later.")
    except Exception as e:
        print(f"[ERROR] Error in handle_custom_time_input: {e}")
        await message.reply("An unexpected error occurred. Please try again later.")


async def prompt_reminder_time(chat_id: int, lang: str):
    print(f"[LOG] prompt_reminder_time, chat_id={chat_id}, lang={lang}")
    try:
        user = get_user(chat_id)
        if not user:
            await bot.send_message(chat_id=chat_id, text="Error: User not found. Please restart the bot with /start.")
            return

        task_time_str = user_tasks.get(chat_id, {}).get("time")
        if not task_time_str:
            await bot.send_message(
                chat_id=chat_id,
                text=translations.get("task_time_missing_error", {}).get(lang, "Task time is missing. Please try again.")
            )
            return

        try:
            task_time = datetime.strptime(task_time_str.strip(), "%H:%M").time()
        except ValueError:
            await bot.send_message(
                chat_id=chat_id,
                text=translations.get("invalid_time_format_error", {}).get(lang, "Invalid task time format. Please try again.")
            )
            return

        timezone_offset = user.get("utc_offset", 0)
        user_timezone = timezone(timedelta(hours=timezone_offset))
        now = datetime.now(timezone.utc).astimezone(user_timezone)

        # Формируем локальное время задачи
        task_datetime = datetime.combine(now.date(), task_time).replace(tzinfo=user_timezone)
        if task_datetime <= now:
            task_datetime += timedelta(days=1)

        remaining_time = (task_datetime - now).total_seconds()
        if remaining_time < 600:
            await bot.send_message(
                chat_id=chat_id,
                reply_markup=create_main_menu(lang),
                text=translations.get("no_reminder_possible", {}).get(lang, "It's too late to set a reminder for this task.")
            )
            return

        reminder_buttons = []
        if remaining_time >= 7 * 24 * 3600:
            reminder_buttons.append(translations.get("reminder_buttons", {}).get(lang, [])[0])
        if remaining_time >= 3600:
            reminder_buttons.append(translations.get("reminder_buttons", {}).get(lang, [])[1])
        if remaining_time >= 600:
            reminder_buttons.append(translations.get("reminder_buttons", {}).get(lang, [])[2])

        reminder_buttons.append(translations.get("cancel_button", {}).get(lang, "Cancel"))

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=button)] for button in reminder_buttons],
            resize_keyboard=True
        )

        user_tasks[chat_id]["waiting_for_reminder_time"] = True

        await bot.send_message(
            chat_id=chat_id,
            text=translations.get("select_reminder_time_prompt", {}).get(lang, "When should I remind you about this task?"),
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"[ERROR] Error in prompt_reminder_time: {e}")
        await bot.send_message(chat_id=chat_id, text="An unexpected error occurred while setting a reminder. Please try again.")


@router.message(lambda message: user_tasks.get(message.from_user.id, {}).get("waiting_for_reminder_time"))
async def handle_reminder_time_selection(message: Message):
    print(f"[LOG] handle_reminder_time_selection, text={message.text}")
    user_id = message.from_user.id

    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            return

        lang = user.get("language", "en")
        timezone_offset = user.get("utc_offset", 0)
        user_timezone = timezone(timedelta(hours=timezone_offset))
        now = datetime.now(timezone.utc).astimezone(user_timezone)

        task_time_str = user_tasks[user_id].get("time")
        if not task_time_str:
            await message.reply(translations["task_time_missing_error"].get(lang, "Task time is missing."))
            return

        try:
            task_time = datetime.strptime(task_time_str.strip(), "%H:%M").time()
        except ValueError:
            await message.reply(translations["invalid_time_format_error"].get(lang, "Invalid task time format. Please try again."))
            return

        task_datetime = datetime.combine(now.date(), task_time).replace(tzinfo=user_timezone)
        if task_datetime <= now:
            task_datetime += timedelta(days=1)

        reminder_offsets = {
            translations["reminder_buttons"][lang][0]: timedelta(days=7),
            translations["reminder_buttons"][lang][1]: timedelta(hours=1),
            translations["reminder_buttons"][lang][2]: timedelta(minutes=10)
        }

        if message.text.strip() in reminder_offsets:
            reminder_offset = reminder_offsets[message.text.strip()]
            reminder_datetime = task_datetime - reminder_offset

            if reminder_datetime <= now:
                await message.reply(translations["invalid_reminder_time"].get(lang, "The reminder time has already passed."))
                return

            user_tasks[user_id]["reminder_time"] = reminder_datetime.strftime("%H:%M")
            user_tasks[user_id].pop("waiting_for_reminder_time", None)
            await message.reply(
                f"{translations['reminder_time_saved'].get(lang, 'Reminder time saved')}: {reminder_datetime.strftime('%H:%M')}"
            )
            await finalize_task_creation(message.chat.id, lang)
            return

        await message.reply(translations["invalid_time_prompt"].get(lang, "Invalid selection. Please choose one of the options."))

    except Exception as e:
        print(f"[ERROR] Error in handle_reminder_time_selection: {e}")
        await message.reply("An unexpected error occurred. Please try again later.")


async def save_task_to_db_via_api(
    user_id: int,
    task_text: str,
    task_date: str,
    task_time: str,
    reminder_time: str = None
):
    print(f"[LOG] save_task_to_db_via_api, user_id={user_id}, task_text='{task_text}'")
    from datetime import datetime
    try:
        datetime.strptime(task_date, "%d.%m.%Y")
        datetime.strptime(task_time, "%H:%M")
        if reminder_time:
            datetime.strptime(reminder_time, "%H:%M")

        result = add_task(
            user_id=user_id,
            task_text=task_text.strip(),
            due_date=task_date.strip(),
            due_time=task_time.strip(),
            reminder_time=reminder_time.strip() if reminder_time else None,
            task_status="in_process"
        )

        if not result:
            raise Exception("Database insertion failed or returned an error.")

        print(f"[INFO] Task successfully saved for user_id={user_id}: {task_text} at {task_date} {task_time}, reminder: {reminder_time}")
    except ValueError as ve:
        print(f"[ERROR] Invalid date or time format for user_id={user_id}: {ve}")
        raise ValueError(f"Invalid date/time format: {ve}")
    except Exception as e:
        print(f"[ERROR] Failed to save task for user_id={user_id}: {e}")
        raise e


async def finalize_task_creation(chat_id: int, lang: str):
    """
    Главное исправление:
    Вместо user_tz.localize(...) используем replace(tzinfo=user_tz).
    """
    print(f"[LOG] finalize_task_creation, chat_id={chat_id}")
    from datetime import datetime

    task = user_tasks.pop(chat_id, None)
    if not task:
        await bot.send_message(
            chat_id=chat_id,
            text=translations["task_creation_error"].get(lang, "Task creation error. Please try again."),
            reply_markup=create_main_menu(lang)
        )
        print(f"[ERROR] Task not found for user_id={chat_id} during finalization.")
        return

    try:
        required_fields = ["text", "day", "time"]
        for field in required_fields:
            if not task.get(field):
                raise KeyError(f"Missing or empty field '{field}' in task details.")

        # Сохраняем задачу в БД
        await save_task_to_db_via_api(
            user_id=chat_id,
            task_text=task["text"],
            task_date=task["day"],
            task_time=task["time"],
            reminder_time=task.get("reminder_time")
        )

        # Получаем только что созданную задачу (чтобы узнать task_id)
        db_cursor.execute("SELECT MAX(task_id) FROM tasks WHERE user_id = ?", (chat_id,))
        row = db_cursor.fetchone()
        if row:
            created_task_id = row[0]
        else:
            created_task_id = None

        if created_task_id:
            user = get_user(chat_id)
            if user:
                # Вместо localize используем replace(tzinfo=...)
                user_offset = user.get("utc_offset", 0)
                user_tz = timezone(timedelta(hours=user_offset))

                due_local_str = f"{task['day']} {task['time']}"
                due_local = datetime.strptime(due_local_str, "%d.%m.%Y %H:%M")
                # Привязываем TZ
                due_local = due_local.replace(tzinfo=user_tz)
                # Переводим в UTC
                due_utc = due_local.astimezone(timezone.utc)

                from scheduler import scheduler, due_job
                from jobs import add_job_record

                # Планируем due_job
                due_job_id = f"due_{created_task_id}"
                scheduler.add_job(
                    due_job,
                    "date",
                    run_date=due_utc,
                    args=[created_task_id, chat_id],
                    id=due_job_id,
                    replace_existing=True
                )
                add_job_record(
                    job_id=due_job_id,
                    task_id=created_task_id,
                    user_id=chat_id,
                    run_time=due_utc.strftime("%Y-%m-%d %H:%M:%S"),
                    job_type="due"
                )

                # Если есть reminder_time
                if task.get("reminder_time"):
                    rem_local_str = f"{task['day']} {task['reminder_time']}"
                    rem_local = datetime.strptime(rem_local_str, "%d.%m.%Y %H:%M")
                    rem_local = rem_local.replace(tzinfo=user_tz)
                    rem_utc = rem_local.astimezone(timezone.utc)

                    reminder_job_id = f"reminder_{created_task_id}"
                    from scheduler import reminder_job
                    scheduler.add_job(
                        reminder_job,
                        "date",
                        run_date=rem_utc,
                        args=[created_task_id, chat_id],
                        id=reminder_job_id,
                        replace_existing=True
                    )
                    add_job_record(
                        job_id=reminder_job_id,
                        task_id=created_task_id,
                        user_id=chat_id,
                        run_time=rem_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        job_type="reminder"
                    )

        await bot.send_message(
            chat_id=chat_id,
            text=translations["task_creation_complete"].get(lang, "Task successfully created!"),
            reply_markup=create_main_menu(lang)
        )
        print(f"[INFO] Task successfully saved for user_id={chat_id}: {task}")

    except KeyError as e:
        print(f"[ERROR] Missing field for user_id={chat_id}: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text=translations["task_creation_error"].get(lang, "Task creation error. Please try again."),
            reply_markup=create_main_menu(lang)
        )
    except ValueError as ve:
        print(f"[ERROR] Invalid date or time for user_id={chat_id}: {ve}")
        await bot.send_message(
            chat_id=chat_id,
            text=translations["invalid_date_or_time"].get(lang, "Invalid date or time format."),
            reply_markup=create_main_menu(lang)
        )
    except Exception as e:
        print(f"[ERROR] Unexpected error for user_id={chat_id}: {e}")
        await bot.send_message(
            chat_id=chat_id,
            text=translations["task_creation_error"].get(lang, "An unexpected error occurred. Please try again."),
            reply_markup=create_main_menu(lang)
        )


@router.message(lambda message: message.text == translations["menu"].get(get_user(message.from_user.id)["language"], [])[1])
async def handle_my_tasks(message: Message):
    print(f"[LOG] handle_my_tasks, text={message.text}")
    try:
        user_id = message.from_user.id
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            print(f"[ERROR] User not found for user_id={user_id}")
            return

        lang = user.get("language", "en")
        tasks = get_user_tasks(user_id)
        if not tasks:
            await message.reply(translations["no_active_tasks"].get(lang, "You have no active tasks."))
            print(f"[INFO] No active tasks for user_id={user_id}")
            return

        task_list = [translations["active_tasks_count"].get(lang, "Active tasks") + f": {len(tasks)}"]
        for idx, task_data in enumerate(tasks, start=1):
            try:
                task_id, task_text, due_date, due_time, status = task_data
                task_details = (
                    f"🔹 {translations['task_number'].get(lang, 'Task')} {idx}:\n"
                    f"- {task_text}\n"
                    f"- {due_date}\n"
                    f"- {due_time}\n"
                )
                task_list.append(task_details)
            except Exception as e:
                print(f"[WARNING] Error processing task for user_id={user_id}: {e}")

        await message.reply("\n\n".join(task_list))
        print(f"[INFO] Sent {len(tasks)} tasks to user_id={user_id}")

    except Exception as e:
        print(f"[ERROR] Error in handle_my_tasks for user_id={message.from_user.id}: {e}")
        await message.reply("An unexpected error occurred. Please try again later.")


def create_main_menu(lang: str) -> ReplyKeyboardMarkup:
    print(f"[LOG] (вторая копия) create_main_menu, lang={lang}")
    try:
        menu_buttons = translations.get("menu", {}).get(lang, [])
        if len(menu_buttons) < 4:
            raise KeyError(f"Insufficient menu buttons for language '{lang}'.")

        keyboard = [
            [KeyboardButton(text=menu_buttons[0]), KeyboardButton(text=menu_buttons[1])],
            [KeyboardButton(text=menu_buttons[2]), KeyboardButton(text=menu_buttons[3])]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

    except KeyError as e:
        print(f"[WARNING] Error in create_main_menu: {e}. Fallback to default menu.")
        fallback_keyboard = [
            [KeyboardButton(text="Add Task"), KeyboardButton(text="My Tasks")],
            [KeyboardButton(text="Stats"), KeyboardButton(text="Settings")]
        ]
        return ReplyKeyboardMarkup(keyboard=fallback_keyboard, resize_keyboard=True)


@router.message()
async def handle_unexpected_message(message: Message):
    print(f"[LOG] handle_unexpected_message, text={message.text}")
    user_id = message.from_user.id
    try:
        user = get_user(user_id)
        if not user:
            await message.reply("Error: User not found. Please restart the bot with /start.")
            print(f"[WARNING] Unexpected message from unknown user_id={user_id}: {message.text}")
            return

        lang = user.get("language", "en")
        print(f"[INFO] Unexpected message from user_id={user_id}, lang={lang}: {message.text}")

        reply_text = translations["unexpected_input"].get(lang, "I didn't understand that. Please use the menu.")
        await message.reply(reply_text)

        await message.answer(
            translations["select_action"].get(lang, "Choose an action:"),
            reply_markup=create_main_menu(lang)
        )

    except Exception as e:
        print(f"[ERROR] Error in handle_unexpected_message for user_id={user_id}: {e}")
        await message.reply("An unexpected error occurred. Please try again.")


@router.callback_query(lambda c: c.data.startswith("complete_") or c.data.startswith("fail_"))
async def handle_task_decision(call: CallbackQuery):
    """
    Обрабатывает нажатие инлайн-кнопок «Выполнено» / «Не выполнено».
    Записывает результат в statistics, удаляет задачу из tasks,
    убирает auto_fail и удаляет сообщение с кнопками.
    """
    user_id = call.from_user.id
    data = call.data

    user = get_user(user_id)

    lang = user.get("language", "en")

    if data.startswith("complete_"):
        task_id_str = data.split("_")[1]
        task_id = int(task_id_str)
        increment_statistics(user_id, "completed")
        delete_task(task_id)

        # Удалить auto_fail, если существует
        auto_fail_job_id = f"auto_fail_{task_id}"
        try:
            scheduler.remove_job(auto_fail_job_id)
        except:
            pass
        remove_job_record(auto_fail_job_id)

        # Отправляем уведомление в чат и всплывающее сообщение
        message_text = translations['task_completed_message'].get(lang, "Task completed ✅")
        await call.message.answer(message_text)  # Сообщение в чат
        await call.answer("✅ " + message_text[:50])  # Всплывающее сообщение (до 50 символов)
        try:
            await call.message.delete()  # Удаляем сообщение с кнопками
        except Exception:
            pass  # Просто игнорируем ошибку

    elif data.startswith("fail_"):
        task_id_str = data.split("_")[1]
        task_id = int(task_id_str)
        increment_statistics(user_id, "failed")
        delete_task(task_id)

        # Удалить auto_fail
        auto_fail_job_id = f"auto_fail_{task_id}"
        try:
            scheduler.remove_job(auto_fail_job_id)
        except:
            pass
        remove_job_record(auto_fail_job_id)

        # Отправляем уведомление в чат и всплывающее сообщение
        message_text = translations['task_failed_message'].get(lang, "Task failed ❌")
        await call.message.answer(message_text)  # Сообщение в чат
        await call.answer("❌ " + message_text[:50])  # Всплывающее сообщение (до 50 символов)
        try:
            await call.message.delete()  # Удаляем сообщение с кнопками
        except Exception:
            pass  # Просто игнорируем ошибку