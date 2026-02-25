import logging
import asyncio
from datetime import datetime, timedelta
from database import (
    water_stats, get_users_for_water_reminders, update_reminder_sent_time, fetch_water_stats_all,
    set_last_reset_water, get_lost_records_of_water, water_reset, add_water_ml, delete_water_log,
    get_users_for_activity_reminders, get_activity_goal_and_today_count, update_activity_reminder_sent_time,
    get_last_exercise_log, get_inactive_users_for_reminder, update_last_inactivity_reminder,
)
from messages import water_quick_reminder_msg, activity_quick_reminder_msg, activity_inactive_reminder_msg
from utils.rate_limit_send import rate_limited_gather

_logger = logging.getLogger(__name__)


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
        _logger.info("Сервис напоминаний запущен")

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
                _logger.error(f"Ошибка в планировщике задач: {e}")
                await asyncio.sleep(60)

    async def _check_all_reminders(self):
        await self._check_water_reminders()
        await self._check_activity_reminders()
        await self._check_inactive_users_reminders()
        await self._check_weekly_water_reset()

    async def _check_water_reminders(self):
        users = await get_users_for_water_reminders()
        now_time_utc = datetime.now() - timedelta(hours=3)
        to_remind = []
        for user_id, broadcast_type, broadcast_interval, last_broadcast, last_update in users:
            if broadcast_type is None:
                continue
            last_update_dt = datetime.fromisoformat(last_update) if last_update else None
            last_broadcast_dt = datetime.fromisoformat(last_broadcast) if last_broadcast else None
            if last_broadcast_dt is None:
                continue
            if broadcast_type == 'Smart':
                if (last_update_dt is None or now_time_utc - last_update_dt >= timedelta(hours=3)) and \
                        now_time_utc - last_broadcast_dt >= timedelta(hours=3):
                    to_remind.append(user_id)
            elif broadcast_type == 'Interval':
                if now_time_utc - last_broadcast_dt >= timedelta(hours=broadcast_interval):
                    to_remind.append(user_id)
        if to_remind:
            coros = [self._send_water_reminder(uid) for uid in to_remind]
            await rate_limited_gather(coros)

    async def _send_water_reminder(self, user_id):
        try:
            current_goal, water_drunk = await water_stats(user_id)
            await self.bot.send_message(user_id, water_quick_reminder_msg(current_goal, water_drunk))
            _logger.info(f"Отправлено напоминание user_id={user_id}")
            await update_reminder_sent_time(user_id)

        except Exception as e:
            _logger.error(f" Ошибка отправки напоминания user_id={user_id}: {e}")

    async def _check_activity_reminders(self):
        users = await get_users_for_activity_reminders()
        now_utc = datetime.utcnow()
        to_remind = []
        for row in users:
            user_id, broadcast_type, broadcast_interval, last_broadcast = row[:4]
            last_broadcast_dt = datetime.fromisoformat(last_broadcast[:19]) if last_broadcast else None
            if last_broadcast_dt is None:
                continue
            elapsed_broadcast = (now_utc - last_broadcast_dt).total_seconds() / 3600
            if broadcast_type == 'Smart':
                last_log = await get_last_exercise_log(user_id)
                last_ex_time = None
                if last_log:
                    try:
                        last_ex_time = datetime.strptime(last_log[1][:19], '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        pass
                elapsed_ex = (now_utc - last_ex_time).total_seconds() / 3600 if last_ex_time else 999
                if elapsed_ex >= 3 and elapsed_broadcast >= 3:
                    to_remind.append(user_id)
            elif broadcast_type == 'Interval' and broadcast_interval:
                if elapsed_broadcast >= broadcast_interval:
                    to_remind.append(user_id)
        if to_remind:
            coros = [self._send_activity_reminder(uid) for uid in to_remind]
            await rate_limited_gather(coros)

    async def _send_activity_reminder(self, user_id):
        try:
            goal, today_count = await get_activity_goal_and_today_count(user_id)
            if goal is None:
                return
            await self.bot.send_message(user_id, activity_quick_reminder_msg(today_count, goal))
            _logger.info(f"Отправлено напоминание активности user_id={user_id}")
            await update_activity_reminder_sent_time(user_id)
        except Exception as e:
            _logger.error(f"Ошибка отправки напоминания активности user_id={user_id}: {e}")

    async def _check_inactive_users_reminders(self):
        user_ids = await get_inactive_users_for_reminder()
        if not user_ids:
            return
        coros = [self._send_inactive_reminder(uid) for uid in user_ids]
        await rate_limited_gather(coros)

    async def _send_inactive_reminder(self, user_id):
        try:
            await self.bot.send_message(user_id, activity_inactive_reminder_msg)
            await update_last_inactivity_reminder(user_id)
            _logger.info(f"Отправлено напоминание неактивному user_id={user_id}")
        except Exception as e:
            _logger.error(f"Ошибка напоминания неактивному user_id={user_id}: {e}")

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
                    _logger.info(f"Пользователь {user_id}: дата сброса обновлена на {last_monday}")
                except Exception as e:
                    _logger.error(f"Пользователь {user_id}: ошибка обновления даты сброса - {e}")
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
                _logger.info(f"Пользователь {user_id}: дата сброса обновлена на {last_monday}")
            except Exception as e:
                _logger.error(f"Пользователь {user_id}: ошибка обновления даты сброса - {e}")
                raise

            # 2. Сбрасываем недельную статистику
            try:
                await water_reset(user_id)
                _logger.info(f"Пользователь {user_id}: недельная статистика обнулена")
            except Exception as e:
                _logger.error(f"Пользователь {user_id}: ошибка сброса статистики - {e}")
                raise

            # 3. Восстанавливаем потерянные записи
            if lost_records > 0:
                try:
                    await add_water_ml(user_id, lost_records,add_total=False)
                    _logger.info(f"Пользователь {user_id}: восстановлено {lost_records} мл за период сброса")
                except Exception as e:
                    _logger.error(f"Пользователь {user_id}: ошибка восстановления {lost_records} мл - {e}")
            else:
                _logger.info(f"Пользователь {user_id}: потерянных записей не найдено")

        except Exception as e:
            _logger.error(f"Пользователь {user_id}: критическая ошибка при сбросе - {e}")
