from datetime import datetime

from database import get_active_exercises, get_exercise_by_id, check_ex_is_favorite, remove_ex_from_favorite, \
    add_ex_to_favorite, get_favorite_exercises, add_exercise_log, get_user_exercise_stats, \
    get_user_exercise_stats_for_exercise, get_last_exercise_log, get_activity_goal_and_today_count
from keyboards import sports_main_menu_keyboard, sports_category_keyboard, sports_difficulty_keyboard, \
    sports_all_pagination_keyboard, sports_exercise_keyboard, sports_favorites_pagination_keyboard, \
    cancel_any_keyboard, sports_confirm_done_keyboard
from messages import sports_main_menu_msg, sports_category_msg, sports_difficulty_msg, sports_ex_list_msg, \
    sports_exercise_details_msg, sports_not_found_ex_msg, sports_favorites_empty_msg, sports_favorites_header_msg, \
    sports_my_stats_msg, sports_my_stats_empty_msg, sports_exercise_done_msg, sports_ex_stats_msg, \
    sports_stats_top_item_msg, sports_confirm_done_msg, sports_done_too_soon_same_msg, sports_done_too_soon_other_msg
from utils.xp_helper import award_xp


def check_can_log_exercise(last_log, exercise_id):
    """
    Логика проверки лимитов времени.
    - Одно и то же упражнение: не чаще раза в 15 минут.
    - Разные упражнения: не чаще раза в 5 минут.
    last_log: (exercise_id, time) или None.
    Возвращает (True, None) или (False, (code, mins)).
    """
    MIN_SAME_EXERCISE_MINUTES = 15
    MIN_OTHER_EXERCISE_MINUTES = 5
    if not last_log:
        return True, None
    last_ex_id, last_time_str = last_log
    try:
        last_time = datetime.strptime(last_time_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return True, None
    now = datetime.utcnow()
    elapsed_minutes = (now - last_time).total_seconds() / 60
    if str(last_ex_id) == str(exercise_id):
        if elapsed_minutes < MIN_SAME_EXERCISE_MINUTES:
            wait_mins = max(0, int(MIN_SAME_EXERCISE_MINUTES - elapsed_minutes) + 1)
            return False, ('same', wait_mins)
    else:
        if elapsed_minutes < MIN_OTHER_EXERCISE_MINUTES:
            wait_mins = max(0, int(MIN_OTHER_EXERCISE_MINUTES - elapsed_minutes) + 1)
            return False, ('other', wait_mins)
    return True, None


async def sports_start(message, bot, first_name=None):
    """
    Главное меню раздела Физ-активность. Вызывается:
    - при нажатии на кнопку "💪 Физ-активность" (после настройки)
    - При выходе из какого-либо подмодуля физ-активности
    """
    first_name = first_name or message.from_user.first_name
    goal, today_count = await get_activity_goal_and_today_count(message.chat.id)
    await bot.send_message(
        message.chat.id,
        sports_main_menu_msg(first_name, goal, today_count),
        reply_markup=sports_main_menu_keyboard()
    )


async def sports_check_all_start(call, bot):
    """
    Запускает просмотр всех упражнений.
    Отправляет пользователю сообщение с выбором категории.
    """
    await bot.edit_message_text(
        sports_category_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_category_keyboard()
    )


async def sports_handle_category(call, bot):
    """
    Обрабатывает выбранную пользователем категорию.
    Отправляет сообщение с выбором уровня сложности.

    Ожидает callback_data вида: sports_category_strength
    Извлекает категорию из последней части.
    """
    category = call.data.split('_')[-1]
    await bot.edit_message_text(
        sports_difficulty_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_difficulty_keyboard(category)
    )


async def sports_show_list(call, bot):
    """
       Показывает список упражнений с пагинацией.
       Обрабатывает:
       - первый показ после выбора сложности
       - переключение страниц
       - возврат к списку из карточки упражнения
       """
    if call.data.startswith('sports_difficulty_'):
        category, difficulty = call.data.split('_')[2:]
        page = 1
    elif call.data.startswith('sport_ex_all_page_'):
        page, category, difficulty = call.data.split('_')[4:]
    elif call.data.startswith('sports_back_to_list_'):
        category, difficulty = call.data.split('_')[4:]
        page = 1
    else:
        return
    ex_info = await get_active_exercises(category, difficulty)
    await bot.edit_message_text(
        sports_ex_list_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_all_pagination_keyboard(
            ex_info, category, difficulty, int(page)
        )
    )


async def sports_show_exercise(call, bot):
    """
    Отображает детальную информацию об упражнении.
     Показывает название, описание, категорию, сложность,
    статус избранного и кнопки действий.
    """
    ex_id = call.data.split('_')[-1]
    ex_info = await get_exercise_by_id(ex_id)
    if not ex_info:
        await bot.answer_callback_query(call.id, sports_not_found_ex_msg)
        return
    ex_name, description, category, difficulty = ex_info[1:5]
    file_id = ex_info[5]
    is_favorite = await check_ex_is_favorite(ex_id, call.message.chat.id)
    await bot.edit_message_text(
        sports_exercise_details_msg(ex_name, description, category,
                                    difficulty, is_favorite, bool(file_id)),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_exercise_keyboard(ex_id, is_favorite, category, difficulty, has_video=bool(file_id))
    )
async def toggle_favorite(call, bot):
    """
    Переключает статус избранного для упражнения.

    Если упражнение уже в избранном — удаляет,
    если нет — добавляет.

    После изменения обновляет отображение упражнения
    вызовом sports_show_exercise.
    """
    ex_id = call.data.split('_')[-1]
    user_id = call.message.chat.id
    is_fav = await check_ex_is_favorite(ex_id, user_id)
    if is_fav:
        await remove_ex_from_favorite(user_id, ex_id)
    else:
        await add_ex_to_favorite(user_id, ex_id)
    await sports_show_exercise(call, bot)


async def sports_check_favorites_start(call, bot):
    """
    Показывает список избранных упражнений пользователя.
    """
    user_id = call.message.chat.id
    favorites = await get_favorite_exercises(user_id)
    if not favorites:
        text = sports_favorites_empty_msg
    else:
        text = sports_favorites_header_msg
    await bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_favorites_pagination_keyboard(favorites, page=1)
    )


async def sports_show_favorites_page(call, bot):
    """
    Обрабатывает переключение страниц в списке избранного.
    """
    page = int(call.data.split('_')[-1])
    user_id = call.message.chat.id
    favorites = await get_favorite_exercises(user_id)
    await bot.edit_message_text(
        sports_favorites_header_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_favorites_pagination_keyboard(favorites, page)
    )


async def sports_back_to_categories(call, bot):
    """
    Возврат от выбора сложности к выбору категории.
    """
    await bot.edit_message_text(
        sports_category_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_category_keyboard()
    )


async def sports_back_to_main(call, bot):
    """
    Возврат в главное меню раздела Физ-активность.
    """
    first_name = call.from_user.first_name
    goal, today_count = await get_activity_goal_and_today_count(call.message.chat.id)
    await bot.edit_message_text(
        sports_main_menu_msg(first_name, goal, today_count),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_main_menu_keyboard()
    )


async def sports_mark_done(call, bot):
    """
    Показывает подтверждение выполнения упражнения.
    """
    ex_id = call.data.split('_')[-1]
    ex_info = await get_exercise_by_id(ex_id)
    if not ex_info:
        await bot.answer_callback_query(call.id, sports_not_found_ex_msg)
        return
    await bot.edit_message_text(
        sports_confirm_done_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_confirm_done_keyboard(ex_id)
    )


async def sports_confirm_done(call, bot):
    """
    Подтверждает выполнение: проверяет лимиты времени, добавляет запись.
    """
    ex_id = call.data.split('_')[-1]
    user_id = call.message.chat.id
    ex_info = await get_exercise_by_id(ex_id)
    if not ex_info:
        await bot.answer_callback_query(call.id, sports_not_found_ex_msg)
        return
    last_log = await get_last_exercise_log(user_id)
    can_log, err = check_can_log_exercise(last_log, ex_id)
    if not can_log:
        code, mins = err
        msg = sports_done_too_soon_same_msg(mins) if code == 'same' else sports_done_too_soon_other_msg(mins)
        await bot.answer_callback_query(call.id, msg, show_alert=True)
        await sports_show_exercise_for_ex_id(call, bot, ex_id)
        return
    await add_exercise_log(user_id, ex_id)
    await bot.answer_callback_query(call.id, sports_exercise_done_msg)
    await sports_show_exercise_for_ex_id(call, bot, ex_id)
    # XP за упражнение
    await award_xp(bot, user_id, 'exercise_done')
    # XP за достижение дневной цели
    goal, today_count = await get_activity_goal_and_today_count(user_id)
    if goal and today_count >= goal:
        await award_xp(bot, user_id, 'exercise_goal')


async def sports_cancel_done(call, bot):
    """
    Отмена подтверждения — возврат к карточке упражнения.
    """
    await bot.answer_callback_query(call.id)
    ex_id = call.data.split('_')[-1]
    await sports_show_exercise_for_ex_id(call, bot, ex_id)


async def sports_show_exercise_for_ex_id(call, bot, ex_id):
    """Показывает карточку упражнения по ex_id (для возврата из подтверждения/отмены)."""
    ex_info = await get_exercise_by_id(ex_id)
    if not ex_info:
        await bot.answer_callback_query(call.id, sports_not_found_ex_msg)
        return
    ex_name, description, category, difficulty = ex_info[1:5]
    file_id = ex_info[5]
    is_favorite = await check_ex_is_favorite(ex_id, call.message.chat.id)
    await bot.edit_message_text(
        sports_exercise_details_msg(ex_name, description, category, difficulty, is_favorite, bool(file_id)),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_exercise_keyboard(ex_id, is_favorite, category, difficulty, has_video=bool(file_id))
    )


async def sports_show_my_stats(call, bot):
    """
    Показывает общую статистику пользователя по выполнению упражнений.
    """
    user_id = call.message.chat.id
    stats = await get_user_exercise_stats(user_id)
    if stats['total'] == 0:
        await bot.edit_message_text(
            sports_my_stats_empty_msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=cancel_any_keyboard()
        )
    else:
        top_list = "\n".join(sports_stats_top_item_msg(name, cnt) for name, cnt in stats['top'])
        text = sports_my_stats_msg(stats['total'], stats['weekly'], top_list)
        await bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=cancel_any_keyboard()
        )


async def sports_show_exercise_stats(call, bot):
    """
    Показывает статистику по конкретному упражнению.
    """
    ex_id = call.data.split('_')[-1]
    user_id = call.message.chat.id
    ex_info = await get_exercise_by_id(ex_id)
    if not ex_info:
        await bot.answer_callback_query(call.id, sports_not_found_ex_msg)
        return
    stats = await get_user_exercise_stats_for_exercise(user_id, ex_id)
    text = sports_ex_stats_msg(stats['total'], stats['weekly'])
    await bot.answer_callback_query(call.id)
    await bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=cancel_any_keyboard()
    )
