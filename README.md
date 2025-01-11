# PlanCheckBot: Your Personal Task Manager Bot 🚀✨

> **A multilingual Telegram bot to manage your tasks, reminders, and statistics, all powered by Python, SQLite, and APScheduler.**  

Hey there, and welcome to **PlanCheckBot**—a cool and handy Telegram bot that helps you keep track of your daily tasks, sends reminders, and even speaks your language! Below, you’ll learn what this bot does, how it’s built, and how you can run it on your own machine.  

---

## 🌟 Features

1. **Multilingual Support**  
   - Choose from English, Russian, or Ukrainian.  
   - All bot messages, menus, and prompts are automatically translated based on user preferences.  

2. **Task Management**  
   - Add tasks with a due date and specific time.  
   - Optional reminders: set up a 7-day, 1-hour, or 10-minute reminder before the task is due.  

3. **Smart Timezone Handling**  
   - Each user can set their **UTC offset** to ensure correct local times for tasks and reminders.  
   - The bot automatically calculates the difference to schedule reminders and due alerts accurately.  

4. **Statistics & Progress Tracking**  
   - Keep track of completed and failed tasks.  
   - Personalized statistics: see how many tasks you’ve done or missed.  

5. **Settings & Customization**  
   - Update your preferred language anytime.  
   - Adjust your local time offset whenever necessary.  

6. **Admin Commands**  
   - **Broadcast**: The admin can send a mass message to all users in their respective languages.  
   - **Users Count**: Check how many users are actively using the bot.  

---

## 🛠 Tech Stack

- **[Python 3.12+](https://www.python.org/)**  
- **[Aiogram 3.x](https://docs.aiogram.dev/)** for Telegram bot functionality.  
- **[SQLite 3](https://www.sqlite.org/index.html)** for local, file-based database.  
- **[APScheduler](https://apscheduler.readthedocs.io/en/stable/)** for scheduling reminders and notifications.  

---

## 📁 Project Structure

```
├─ main.py         # Entry point of the bot; starts polling, sets up HTTP server
├─ handlers.py     # All message/command handlers (add task, list tasks, stats, settings, etc.)
├─ database.py     # Database models & queries (SQLite): users, tasks, statistics, jobs
├─ jobs.py         # Functions to add/remove APScheduler jobs & store them in DB
├─ scheduler.py    # APScheduler initialization & scheduling logic
├─ translations.py # All text translations (ru, en, ua, etc.)
├─ config.py       # (Optional) Configuration settings, constants, tokens
└─ requirements.txt # Python dependencies
```

**Key Points**:  
1. **`database.py`**: Initializes and manages the SQLite database. It creates tables (`users`, `tasks`, `statistics`, `jobs`) and exposes functions like `add_task()`, `get_all_users()`, etc.  
2. **`handlers.py`**: Uses Aiogram’s routing system to capture messages and execute logic:
   - `/start` to register new users.
   - `/broadcast` (admin only) to send mass messages in each user’s language.
   - Task workflow (adding tasks, selecting date/time, setting reminders).
   - Viewing tasks & stats.  
3. **`scheduler.py`**: Sets up the APScheduler, restoring jobs from the DB and scheduling `reminder_job` and `due_job`.  
4. **`jobs.py`**: Functions that handle APScheduler tasks (e.g., add job records, remove them, track them in the `jobs` table).  

---

## 🚀 Quick Start

1. **Clone the Repo**  
   ```bash
   git clone https://github.com/YourUsername/PlanCheckBot.git
   cd PlanCheckBot
   ```

2. **Install Dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment**  
   - In `config.py` (or `.env`), specify your **Telegram Bot Token** and, optionally, your **Admin ID**.  
   - Example in `config.py`:
     ```python
     BOT_TOKEN = "123456:ABC-YourBotToken"
     ADMIN_ID = 987654321
     ```
     
4. **Run the Bot**  
   ```bash
   python main.py
   ```
   You should see logs indicating the bot has started polling Telegram and the scheduler is up.

5. **Add the Bot in Telegram**  
   - Open Telegram, find your bot via `@YourBotUsername`, and press **Start**.
   - Choose your preferred language.
   - Follow the menu prompts to add tasks, check statistics, and set reminders!  

---

## 🧩 How It Works

1. **User Registration**  
   - On `/start`, the bot saves user data (including language & UTC offset) in the `users` table.  

2. **Task Workflow**  
   - **Add Task**: The user provides a **task text**, then selects a **day** and **time**, plus an optional **reminder**.  
   - **Scheduler**: Each task is saved in `tasks` and scheduled via APScheduler. The job ID goes into the `jobs` table.  

3. **Reminders & Deadlines**  
   - **Reminder**: N minutes/hours/days before the due time, the scheduler sends a reminder.  
   - **Due**: At the exact task time, the bot pings the user.  

4. **Completion & Statistics**  
   - User can mark tasks as **Completed** ✅ or **Failed** ❌.  
   - Stats are stored in `statistics` (completed/failed counts).  

5. **Admin Tools**  
   - `/broadcast`: Admin can instantly send a mass message to all users—each in their chosen language!  
   - `/users_count`: Shows how many total users exist in the `users` table.  

---

## 🤝 Contributing

Feel free to open issues or pull requests if you find bugs or want to add more features. Let’s make the bot more awesome together!  

---

## 📄 License

This project is distributed under the [MIT License](LICENSE). Use it freely, customize it, and distribute it.  

---

## 💬 Thanks for Stopping By!

If you find **PlanCheckBot** useful, please ⭐ the repo or share with friends.  
Enjoy your new personal task manager & scheduler bot!  

> _Happy Tasking!_  
> **— The PlanCheckBot Team**  