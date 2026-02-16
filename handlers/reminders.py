import logging
import time
import asyncio
from datetime import datetime, timedelta
from database import water_stats, get_users_for_water_reminders, update_reminder_sent_time
from messages import water_quick_reminder_msg

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
        self.task = None
        self.check_interval = 120  # секунд

    async def start(self):
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._check_loop())
        logging.info("Сервис напоминаний запущен")

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _check_loop(self):
        while self.running:
            try:
                await self._check_all_reminders()
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Ошибка проверки напоминаний: {e}")
                await asyncio.sleep(60)

    async def _check_all_reminders(self):
        await self._check_water_reminders()

    async def _check_water_reminders(self):
        users = await get_users_for_water_reminders()
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
                    await self._send_water_reminder(user_id)
            elif broadcast_type == 'Interval':
                if now_time_utc - \
                        last_broadcast >= timedelta(hours=broadcast_interval):
                    await self._send_water_reminder(user_id)

    async def _send_water_reminder(self, user_id):
        try:
            current_goal, water_drunk = await water_stats(user_id)
            await self.bot.send_message(user_id, water_quick_reminder_msg(current_goal, water_drunk))
            logging.info(f"Отправлено напоминание user_id={user_id}")
            await update_reminder_sent_time(user_id)

        except Exception as e:
            logging.error(f" Ошибка отправки напоминания user_id={user_id}: {e}")
