import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

from database import (
    add_water_ml,
    clear_stale_ticket_locks,
    delete_water_log,
    fetch_water_stats_all,
    get_activity_goal_and_today_count,
    get_all_sleep_settings_for_quiet_hours,
    get_inactive_users_for_reminder,
    get_last_exercise_log,
    get_last_notification,
    get_lost_records_of_water,
    get_open_sleep_session,
    get_users_for_activity_reminders,
    get_users_for_sleep_reminders,
    get_users_for_water_reminders,
    set_last_reset_water,
    update_activity_reminder_sent_time,
    update_last_inactivity_reminder,
    update_last_notification,
    update_reminder_sent_time,
    update_sleep_last_sleep_reminder,
    update_sleep_last_wake_reminder,
    water_reset,
    water_stats,
)
from keyboards import sleep_bedtime_reminder_keyboard, sleep_wakeup_reminder_keyboard
from messages import (
    activity_inactive_reminder_msg,
    activity_quick_reminder_msg,
    sleep_reminder_before_msg,
    sleep_reminder_wakeup_msg,
    water_quick_reminder_msg,
)
from utils.rate_limit_send import rate_limited_gather

_logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, bot: Any) -> None:
        """Инициализирует планировщик с экземпляром бота."""
        self.bot = bot
        self.running = False
        self.task = None
        self.check_interval = 120  # секунд
        self._last_ticket_lock_cleanup = datetime.min

    async def start(self) -> None:
        """Запускает фоновый цикл проверки напоминаний."""
        if self.running:
            return
        self.running = True
        self.task = asyncio.create_task(self._check_loop())
        _logger.info("Сервис напоминаний запущен")

    async def stop(self) -> None:
        """Останавливает планировщик и отменяет фоновую задачу."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _check_loop(self) -> None:
        """Бесконечный цикл с периодическим запуском всех проверок напоминаний."""
        while self.running:
            try:
                await self._check_all_reminders()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                _logger.error(f"Ошибка в планировщике задач: {e}")
                await asyncio.sleep(60)

    async def _check_all_reminders(self) -> None:
        """Запускает все типы проверок напоминаний за один цикл."""
        quiet_hours = await get_all_sleep_settings_for_quiet_hours()
        await self._check_water_reminders(quiet_hours)
        await self._check_activity_reminders(quiet_hours)
        await self._check_inactive_users_reminders(quiet_hours)
        await self._check_sleep_reminders()
        await self._check_weekly_water_reset()
        await self._cleanup_stale_ticket_locks()

    async def _cleanup_stale_ticket_locks(self) -> None:
        """Очищает устаревшие блокировки тикетов каждые 20 минут."""
        now = datetime.utcnow()
        if now - self._last_ticket_lock_cleanup < timedelta(minutes=20):
            return
        self._last_ticket_lock_cleanup = now
        cleared = await clear_stale_ticket_locks(max_age_hours=1)
        if cleared:
            _logger.info(f"Stale ticket locks cleared: {cleared}")

    @staticmethod
    def _is_quiet_hours(user_id: int, quiet_hours: dict) -> bool:
        """Возвращает True, если текущее время пользователя попадает в окно сна."""
        if user_id not in quiet_hours:
            return False
        sleep_time_str, wake_time_str, tz = quiet_hours[user_id]
        now_user = datetime.now() + timedelta(hours=tz)
        now_min = now_user.hour * 60 + now_user.minute
        sleep_h, sleep_m = map(int, sleep_time_str.split(':'))
        wake_h, wake_m = map(int, wake_time_str.split(':'))
        sleep_min = sleep_h * 60 + sleep_m
        wake_min = wake_h * 60 + wake_m
        if sleep_min > wake_min:  # переходит через полночь (напр. 23:00 → 07:00)
            return now_min >= sleep_min or now_min < wake_min
        else:
            return sleep_min <= now_min < wake_min

    async def _check_water_reminders(self, quiet_hours: dict | None = None) -> None:
        """Определяет пользователей, которым нужно отправить напоминание о воде, и рассылает его."""
        users = await get_users_for_water_reminders()
        now_time_utc = datetime.now() - timedelta(hours=3)
        to_remind = []
        for user_id, broadcast_type, broadcast_interval, last_broadcast, last_update in users:
            if broadcast_type is None:
                continue
            if quiet_hours and self._is_quiet_hours(user_id, quiet_hours):
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

    async def _send_water_reminder(self, user_id: int) -> None:
        """Отправляет одно напоминание о воде конкретному пользователю и обновляет время отправки."""
        try:
            last_notif = await get_last_notification(user_id)
            if last_notif and (datetime.utcnow() - last_notif).total_seconds() < 15 * 60:
                return
            current_goal, water_drunk = await water_stats(user_id)
            await self.bot.send_message(user_id, water_quick_reminder_msg(current_goal, water_drunk))
            _logger.info(f"Отправлено напоминание ID пользователя={user_id}")
            await update_reminder_sent_time(user_id)
            await update_last_notification(user_id)

        except Exception as e:
            _logger.error(f"Ошибка отправки напоминания ID пользователя={user_id}: {e}")

    async def _check_activity_reminders(self, quiet_hours: dict | None = None) -> None:
        """Определяет пользователей, которым нужно напомнить об активности, и рассылает напоминания."""
        users = await get_users_for_activity_reminders()
        now_utc = datetime.utcnow()
        to_remind = []
        for row in users:
            user_id, broadcast_type, broadcast_interval, last_broadcast = row[:4]
            if quiet_hours and self._is_quiet_hours(user_id, quiet_hours):
                continue
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

    async def _send_activity_reminder(self, user_id: int) -> None:
        """Отправляет одно напоминание об активности конкретному пользователю."""
        try:
            last_notif = await get_last_notification(user_id)
            if last_notif and (datetime.utcnow() - last_notif).total_seconds() < 15 * 60:
                return
            goal, today_count = await get_activity_goal_and_today_count(user_id)
            if goal is None:
                return
            await self.bot.send_message(user_id, activity_quick_reminder_msg(today_count, goal))
            _logger.info(f"Отправлено напоминание активности ID пользователя={user_id}")
            await update_activity_reminder_sent_time(user_id)
            await update_last_notification(user_id)
        except Exception as e:
            _logger.error(f"Ошибка отправки напоминания активности ID пользователя={user_id}: {e}")

    async def _check_inactive_users_reminders(self, quiet_hours: dict | None = None) -> None:
        """Отправляет мотивационные напоминания давно неактивным пользователям."""
        user_ids = await get_inactive_users_for_reminder()
        if not user_ids:
            return
        if quiet_hours:
            user_ids = [uid for uid in user_ids if not self._is_quiet_hours(uid, quiet_hours)]
        if not user_ids:
            return
        coros = [self._send_inactive_reminder(uid) for uid in user_ids]
        await rate_limited_gather(coros)

    async def _send_inactive_reminder(self, user_id: int) -> None:
        """Отправляет напоминание неактивному пользователю и обновляет время последнего напоминания."""
        try:
            last_notif = await get_last_notification(user_id)
            if last_notif and (datetime.utcnow() - last_notif).total_seconds() < 15 * 60:
                return
            await self.bot.send_message(user_id, activity_inactive_reminder_msg)
            await update_last_inactivity_reminder(user_id)
            await update_last_notification(user_id)
            _logger.info(f"Отправлено напоминание неактивному ID пользователя={user_id}")
        except Exception as e:
            _logger.error(f"Ошибка напоминания неактивному ID пользователя={user_id}: {e}")

    async def _check_sleep_reminders(self) -> None:
        """Проверяет и рассылает напоминания об отбое и подъёме согласно расписанию каждого пользователя."""
        users = await get_users_for_sleep_reminders()
        for user_id, sleep_time_str, wake_time_str, tz, last_sleep_rem, last_wake_rem, last_notif_str in users:
            tz = tz or 0
            now_user = datetime.now() + timedelta(hours=tz)
            now_min = now_user.hour * 60 + now_user.minute

            sleep_h, sleep_m = map(int, sleep_time_str.split(':'))
            wake_h, wake_m = map(int, wake_time_str.split(':'))
            sleep_min = sleep_h * 60 + sleep_m
            wake_min = wake_h * 60 + wake_m

            # Вычисляем время последнего уведомления (UTC-сравнение)
            last_notif_dt = None
            if last_notif_str:
                try:
                    last_notif_dt = datetime.fromisoformat(last_notif_str[:19])
                except Exception:
                    pass
            now_utc = datetime.utcnow()

            def _within_15min_limit() -> bool:
                """Возвращает True, если последнее уведомление было менее 15 минут назад."""
                if last_notif_dt is None:
                    return False
                return (now_utc - last_notif_dt).total_seconds() < 15 * 60

            # Окно напоминания "пора спать": за [35, 5] мин до отбоя
            sleep_window_start = (sleep_min - 35) % 1440
            sleep_window_end = (sleep_min - 5) % 1440

            def _in_window(now_m: int, start_m: int, end_m: int) -> bool:
                """Проверяет, попадает ли текущее время (в минутах с начала дня) в заданное временнóе окно."""
                if start_m <= end_m:
                    return start_m <= now_m <= end_m
                else:  # перехлёст через полночь
                    return now_m >= start_m or now_m <= end_m

            # Напоминание о сне
            if _in_window(now_min, sleep_window_start, sleep_window_end):
                last_dt = datetime.fromisoformat(last_sleep_rem[:19]) if last_sleep_rem else None
                if last_dt is None or (now_user - last_dt).total_seconds() > 20 * 3600:
                    if not _within_15min_limit():
                        try:
                            await self.bot.send_message(
                                user_id,
                                sleep_reminder_before_msg(sleep_time_str),
                                reply_markup=sleep_bedtime_reminder_keyboard()
                            )
                            await update_sleep_last_sleep_reminder(user_id)
                            await update_last_notification(user_id)
                            last_notif_dt = now_utc  # обновляем локально для следующей проверки
                            _logger.info(f"Отправлено напоминание об отбое ID пользователя={user_id}")
                        except Exception as e:
                            _logger.error(f"Ошибка напоминания об отбое ID пользователя={user_id}: {e}")

            # Окно напоминания "доброе утро": [wake_time - 5, wake_time + 5]
            wake_window_start = (wake_min - 5) % 1440
            wake_window_end = (wake_min + 5) % 1440
            if _in_window(now_min, wake_window_start, wake_window_end):
                last_dt = datetime.fromisoformat(last_wake_rem[:19]) if last_wake_rem else None
                if last_dt is None or (now_user - last_dt).total_seconds() > 20 * 3600:
                    if not _within_15min_limit():
                        # Отправляем уведомление о пробуждении только если есть активная сессия сна
                        open_session = await get_open_sleep_session(user_id)
                        if open_session is None:
                            _logger.info(f"Пропущено напоминание о подъёме (нет открытой сессии сна) ID пользователя={user_id}")
                        else:
                            try:
                                await self.bot.send_message(
                                    user_id,
                                    sleep_reminder_wakeup_msg(wake_time_str),
                                    reply_markup=sleep_wakeup_reminder_keyboard()
                                )
                                await update_sleep_last_wake_reminder(user_id)
                                await update_last_notification(user_id)
                                _logger.info(f"Отправлено напоминание о подъёме ID пользователя={user_id}")
                            except Exception as e:
                                _logger.error(f"Ошибка напоминания о подъёме ID пользователя={user_id}: {e}")

    @staticmethod
    async def _check_weekly_water_reset() -> None:
        """Запускает еженедельный сброс водной статистики для пользователей, у которых наступил новый понедельник."""
        users = await fetch_water_stats_all()
        for user_id, goal_ml,timezone, _, _, \
                _, _, _, _, _, last_reset_str in users:
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
    async def _weekly_water_reset(user_id: int, last_monday: Any, lost_records: int) -> None:
        """Выполняет еженедельный сброс водной статистики: обновляет дату сброса, обнуляет недельные данные и восстанавливает потерянные записи."""
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

