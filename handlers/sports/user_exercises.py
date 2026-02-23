from unicodedata import name

from database import get_active_exercises, get_exercise_by_id, check_ex_is_favorite, remove_ex_from_favorite, \
    add_ex_to_favorite
from keyboards import sports_main_menu_keyboard, sports_category_keyboard, sports_difficulty_keyboard, \
    sports_all_pagination_keyboard, sports_exercise_keyboard
from messages import sports_main_menu_msg, sports_category_msg, sports_difficulty_msg, sports_ex_list_msg, \
    sports_exercise_details_msg, sports_not_found_ex_msg


async def sports_start(message, bot, first_name=None):
    """
    Главное меню раздела Физ-активность. Вызывается:
    - при нажатии на кнопку "💪 Физ-активность"
    - При выходе из какого-либо подмодуля физ-активности
    """
    first_name = first_name or message.from_user.first_name
    await bot.send_message(
        message.chat.id,
        sports_main_menu_msg(first_name),
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
    is_favorite = await check_ex_is_favorite(ex_id, call.message.chat.id)
    await bot.edit_message_text(
        sports_exercise_details_msg(ex_name, description, category,
                                    difficulty, is_favorite),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=sports_exercise_keyboard(ex_id, is_favorite, category, difficulty)
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
