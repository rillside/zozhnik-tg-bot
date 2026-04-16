"""Утилита для начисления XP и отправки уведомлений об этом."""
from typing import Any
from database import add_xp
from messages import level_up_msg, xp_gained_msg

XP_PER_LEVEL = 100
XP_REWARDS = {
    'water_add': 5,
    'water_goal': 20,
    'exercise_done': 10,
    'exercise_goal': 30,
    'sleep_good': 40,
    'sleep_ok': 20,
    'sleep_short': 5,
    'streak_bonus': 15,
}

XP_ACTION_NAMES = {
    'water_add': 'добавление воды',
    'water_goal': 'выполнение цели по воде',
    'exercise_done': 'выполнение упражнения',
    'exercise_goal': 'достижение цели по активности',
    'sleep_good': 'отличный сон',
    'sleep_ok': 'нормальный сон',
    'sleep_short': 'отметку сна',
    'streak_bonus': 'ежедневный заход',
}


async def award_xp(bot: Any, user_id: int, action: str, silent: bool = False) -> dict:
    """
    Начисляет XP и отправляет сообщение пользователю.
    silent=True — не отправлять уведомление.
    Возвращает результат add_xp.
    """
    result = await add_xp(user_id, action, xp_rewards=XP_REWARDS, xp_per_level=XP_PER_LEVEL)
    if result['xp_gained'] == 0:
        return result
    if not silent:
        if result['leveled_up']:
            await bot.send_message(user_id, level_up_msg(result['new_level'], result['total_xp']))
        else:
            action_name = XP_ACTION_NAMES.get(action, action)
            await bot.send_message(
                user_id,
                xp_gained_msg(action_name, result['xp_gained'], result['total_xp'], result['new_level'])
            )
    return result
