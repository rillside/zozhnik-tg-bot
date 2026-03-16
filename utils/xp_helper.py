"""Утилита для начисления XP и отправки уведомлений об этом."""
from database import add_xp
from messages import xp_gained_msg, level_up_msg


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


async def award_xp(bot, user_id: int, action: str, silent: bool = False) -> dict:
    """
    Начисляет XP и отправляет сообщение пользователю.
    silent=True — не отправлять уведомление.
    Возвращает результат add_xp.
    """
    result = await add_xp(user_id, action)
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
