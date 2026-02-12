import logging
import threading
import time
from datetime import datetime, timedelta

from database import water_stats, get_users_for_water_reminders, update_reminder_sent_time
from messages import  water_quick_reminder_msg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)


class UniversalReminderService:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.thread = None
        self.check_interval = 600  # секунд

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(
            target=self._check_loop,
            daemon=True,
            name="UniversalReminderThread"
        )
        self.thread.start()
        logging.info("Сервис напоминаний запущен")

    def stop(self):
        self.running = False
        self.thread.join(timeout=10)

    def _check_loop(self):
        while self.running:
            try:
             self._check_all_reminders()
            except Exception as e:
             logging.error(f"Ошибка проверки напоминаний: {e}")

            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_all_reminders(self):
        self._check_water_reminders()

    def _check_water_reminders(self):
        users = get_users_for_water_reminders()
        for user_id, broadcast_type, broadcast_interval, last_broadcast, \
                last_update in users:
            now_time_utc = datetime.now() - timedelta(hours=3)
            last_update = datetime.fromisoformat(last_update) if last_update else None
            last_broadcast = datetime.fromisoformat(last_broadcast)
            if broadcast_type == 'Smart':
                if (last_update is None or now_time_utc -
                    last_update >=
                    timedelta(hours=3)) and \
                        now_time_utc - last_broadcast >= \
                        timedelta(hours=3):
                    self._send_water_reminder(user_id)
            elif broadcast_type == 'Interval':
                if now_time_utc - \
                        last_broadcast >= timedelta(hours=broadcast_interval):
                    self._send_water_reminder(user_id)

    def _send_water_reminder(self, user_id):
        try:
            current_goal, water_drunk = water_stats(user_id)
            self.bot.send_message(user_id, water_quick_reminder_msg(current_goal, water_drunk))
            logging.info(f"Отправлено напоминание user_id={user_id}")
            update_reminder_sent_time(user_id)

        except Exception as e:
            logging.error(f" Ошибка отправки напоминания user_id={user_id}: {e}")
