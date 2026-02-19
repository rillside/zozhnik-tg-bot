import logging
import asyncio
from datetime import datetime, timedelta
from database import water_stats, get_users_for_water_reminders, update_reminder_sent_time, fetch_water_stats_all, \
    set_last_reset_water, get_lost_records_of_water, water_reset, add_water_ml, delete_water_log
from messages import water_quick_reminder_msg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)


class Scheduler:
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
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Ошибка в планировщике задач: {e}")
                await asyncio.sleep(60)

    async def _check_all_reminders(self):
        await self._check_water_reminders()
        await self._check_weekly_water_reset()

    async def _check_water_reminders(self):
        users = await get_users_for_water_reminders()
        for user_id, broadcast_type, broadcast_interval, last_broadcast, \
                last_update in users:
            if broadcast_type is None:
                continue
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

    @staticmethod
    async def _check_weekly_water_reset():
        users = await fetch_water_stats_all()
        for user_id, goal_ml,timezone, Monday, Tuesday, \
                Wednesday, Thursday, Friday, Saturday, Sunday, last_reset_str in users:
            if goal_ml is None:
                continue
            last_reset = datetime.strptime(last_reset_str, '%Y-%m-%d').date() if last_reset_str else None
            now_time_user = datetime.now() + timedelta(hours=int(timezone))
            now_user_date = now_time_user.date()
            days_since_monday = now_user_date.weekday()
            last_monday = now_user_date - timedelta(days=days_since_monday)
            if last_reset is None:
                try:
                    await set_last_reset_water(user_id, last_monday)
                    logging.info(f"Пользователь {user_id}: дата сброса обновлена на {last_monday}")
                except Exception as e:
                    logging.error(f"Пользователь {user_id}: ошибка обновления даты сброса - {e}")
                    raise
            elif last_reset < last_monday:
                logs_by_user = await get_lost_records_of_water(user_id)
                lost_records = 0
                for log_id,amount, week_start in logs_by_user:
                    week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
                    if week_start_date == last_monday:
                        lost_records += amount
                        await delete_water_log(log_id)
                await Scheduler._weekly_water_reset(user_id, last_monday, lost_records)

    @staticmethod
    async def _weekly_water_reset(user_id, last_monday, lost_records):
        try:
            # 1. Обновляем дату последнего сброса
            try:
                await set_last_reset_water(user_id, last_monday)
                logging.info(f"Пользователь {user_id}: дата сброса обновлена на {last_monday}")
            except Exception as e:
                logging.error(f"Пользователь {user_id}: ошибка обновления даты сброса - {e}")
                raise

            # 2. Сбрасываем недельную статистику
            try:
                await water_reset(user_id)
                logging.info(f"Пользователь {user_id}: недельная статистика обнулена")
            except Exception as e:
                logging.error(f"Пользователь {user_id}: ошибка сброса статистики - {e}")
                raise

            # 3. Восстанавливаем потерянные записи
            if lost_records > 0:
                try:
                    await add_water_ml(user_id, lost_records,add_total=False)
                    logging.info(f"Пользователь {user_id}: восстановлено {lost_records} мл за период сброса")
                except Exception as e:
                    logging.error(f"Пользователь {user_id}: ошибка восстановления {lost_records} мл - {e}")
            else:
                logging.info(f"Пользователь {user_id}: потерянных записей не найдено")

        except Exception as e:
            logging.error(f"Пользователь {user_id}: критическая ошибка при сбросе - {e}")
