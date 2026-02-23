import asyncio
from database import add_exercise_to_db, is_exercise_name_exists, get_exercises_id_name, get_exercise_by_id, \
    get_file_id_by_ex_id, update_exercise_in_db, get_exercise_status, delete_exercise_in_db, get_exercise_stats
from keyboards import admin_exercise_keyboard, exercise_navigation_keyboard, ex_difficulty_keyboard, \
    ex_category_keyboard, \
    exercise_confirm_keyboard, cancel_media_keyboard, exercise_category_filter_keyboard, \
    exercise_difficulty_filter_keyboard, edit_ex_pagination_keyboard, no_exercises_keyboard, exercise_edit_keyboard, \
    exercise_edit_cancel_keyboard, ex_confirm_delete_keyboard, cancel_any_keyboard
from messages import admin_exercise_menu_msg, exercise_request_name_msg, exercise_name_too_long_msg, \
    exercise_request_description_msg, exercise_description_too_short_msg, exercise_description_too_long_msg, \
    exercise_request_category_msg, exercise_request_difficulty_msg, exercise_request_video_msg, \
    error_msg, exercise_name_exists, exercise_saved_msg, exercise_confirm_msg, exercise_add_error, step_back_msg, \
    aggressive_exercise_info_msg, edit_exercise_category_msg, edit_exercise_difficulty_msg, \
    no_exercises_found_msg, exercises_list_header_msg, exercise_full_details_msg, edit_exercise_field_name_msg, \
    edit_exercise_field_description_msg, edit_exercise_field_category_msg, edit_exercise_field_difficulty_msg, \
    edit_exercise_field_video_msg, exercise_edit_error_msg, confirm_delete_exercise_msg, exercise_deleted_msg, \
    cancellation, exercise_stats_msg
from utils.censorship.checker import censor_check, removal_of_admin_rights
from utils.fsm import set_state, get_state, clear_state_keep_data, clear_state


def get_validated_data(user_id):
    """
    Проверяет наличие всех обязательных полей.
    Возвращает кортеж значений, если все поля есть, иначе False
    """
    data = get_state(user_id)[1]
    if isinstance(data, dict):
        name = data.get('name')
        description = data.get('description')
        category = data.get('category')
        difficulty = data.get('difficulty')
        file_id = data.get('video')
    else:
        return False
    if not all([name, description, category, difficulty, file_id]):
        return False
    return name, description, category, difficulty, file_id


async def validate_exercise_censorship(name, description):
    """
    Проверяет все поля упражнения на цензуру параллельно
    """

    # Запускаем проверки параллельно
    tasks = [censor_check(name), censor_check(description)]
    results = await asyncio.gather(*tasks)

    # Ищем первое нарушение
    if  not all(results):
        return False

    return True


async def exercise_management(message, bot, first_name=None):
    first_name = first_name or message.from_user.first_name
    await bot.send_message(message.chat.id, admin_exercise_menu_msg(
        first_name),
                           reply_markup=admin_exercise_keyboard()
                           )


async def handle_exercise_accept(user_id, bot):
    res = get_validated_data(user_id)
    if res:
        name, description, category, difficulty, file_id = get_validated_data(user_id)
    else:
        await bot.send_message(user_id, exercise_add_error)
        return False

    await bot.send_message(
        user_id,
        exercise_confirm_msg(
            name,
            description,
            category,
            difficulty
        ),
        reply_markup=exercise_confirm_keyboard()
    )
    return True


async def save_exercise(user_id, username, bot):
    res = get_validated_data(user_id)
    if res:
        name, description, category, difficulty, file_id = get_validated_data(user_id)
        if await validate_exercise_censorship(name, description):
            await add_exercise_to_db(name, description, category, difficulty, file_id, user_id)
            await bot.send_message(user_id, exercise_saved_msg(name),
                                   reply_markup=admin_exercise_keyboard())
        else:
            await removal_of_admin_rights(bot, aggressive_exercise_info_msg(name, description), user_id, username,
                                          'exercise')
    else:
        await bot.send_message(user_id, exercise_add_error)


async def exercise_go_back(call, bot):
    """Обработка кнопки Назад при добавлении упражнения"""
    state, data = get_state(call.message.chat.id)

    if state != 'adding_exercise':
        await bot.answer_callback_query(call.id, error_msg)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        return

    # Определяем текущий шаг по наличию ключей и откатываем
    if 'video' in data:
        # Откат к отправке видео
        del data['video']
        text = exercise_request_video_msg
        keyboard = exercise_navigation_keyboard(step=5)

    elif 'difficulty' in data:
        # Откат к уровню сложности
        del data['difficulty']
        text = exercise_request_difficulty_msg
        keyboard = ex_difficulty_keyboard()

    elif 'category' in data:
        # Откат к категории
        del data['category']
        text = exercise_request_category_msg
        keyboard = ex_category_keyboard()

    elif 'description' in data:
        # Откат к описанию
        del data['description']
        text = exercise_request_description_msg
        keyboard = exercise_navigation_keyboard(step=2)

    elif 'name' in data:
        # Откат к имени
        del data['name']
        text = exercise_request_name_msg
        keyboard = exercise_navigation_keyboard(step=1)

    else:
        await bot.answer_callback_query(call.id, error_msg)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        return

    set_state(call.message.chat.id, 'adding_exercise', data)
    await bot.answer_callback_query(call.id, step_back_msg)
    await bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


async def start_add_exercise(call, bot):
    """Начать добавление упражнения"""
    set_state(call.message.chat.id, 'adding_exercise', {})
    await bot.send_message(call.message.chat.id,
                           exercise_request_name_msg,
                           reply_markup=exercise_navigation_keyboard(step=1)
                           )


async def handle_exercise_name(message, bot):
    """Обработка названия"""
    state, data = get_state(message.chat.id)
    if await is_exercise_name_exists(message.text):
        await bot.send_message(
            message.chat.id,
            exercise_name_exists,
            reply_markup=exercise_navigation_keyboard(step=1)
        )
        return
    if len(message.text) > 50:
        await bot.send_message(message.chat.id,
                               exercise_name_too_long_msg,
                               reply_markup=exercise_navigation_keyboard(step=1))
        return

    data['name'] = message.text
    set_state(message.chat.id, 'adding_exercise', data)

    await bot.send_message(message.chat.id,
                           exercise_request_description_msg,
                           reply_markup=exercise_navigation_keyboard(step=2)
                           )


async def handle_exercise_description(message, bot):
    """Обработка описания"""
    state, data = get_state(message.chat.id)

    if len(message.text) < 20:
        await bot.send_message(message.chat.id,
                               exercise_description_too_short_msg,
                               reply_markup=exercise_navigation_keyboard(step=2))
        return

    if len(message.text) > 500:
        await bot.send_message(message.chat.id,
                               exercise_description_too_long_msg,
                               reply_markup=exercise_navigation_keyboard(step=2))
        return

    data['description'] = message.text
    set_state(message.chat.id, 'adding_exercise', data)

    await bot.send_message(message.chat.id,
                           exercise_request_category_msg,
                           reply_markup=ex_category_keyboard())


async def handle_exercise_category(call, bot):
    """Обработка категории"""
    state, data = get_state(call.message.chat.id)
    if state != 'adding_exercise':
        await bot.send_message(call.message.chat.id, exercise_add_error)
        return
    data['category'] = call.data.split('_')[-1]  # например 'strength'
    set_state(call.message.chat.id, 'adding_exercise', data)

    await bot.edit_message_text(
        exercise_request_difficulty_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=ex_difficulty_keyboard()
    )


async def handle_exercise_difficulty(call, bot):
    """Обработка сложности"""
    state, data = get_state(call.message.chat.id)
    if state != 'adding_exercise':
        await bot.send_message(call.message.chat.id, exercise_add_error)
        return
    data['difficulty'] = call.data.split('_')[-1]  # например 'beginner'
    set_state(call.message.chat.id, 'adding_exercise', data)

    await bot.edit_message_text(
        exercise_request_video_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=exercise_navigation_keyboard(step=5)
    )


async def handle_exercise_video(message, bot):
    """Обработка видео"""
    state, data = get_state(message.chat.id)
    file_id = message.video.file_id if message.video else message.animation.file_id
    data['video'] = file_id
    clear_state_keep_data(message.chat.id)
    await handle_exercise_accept(message.chat.id, bot)


async def open_video(call, bot, is_moment_of_creation=True):
    if is_moment_of_creation:
        res = get_validated_data(call.message.chat.id)
        if res:
            file_id = res[-1]
        else:
            await bot.send_message(call.message.chat.id, exercise_add_error)
            return
    else:
        exercise_id = call.data.split('_')[-1]
        file_id = await get_file_id_by_ex_id(exercise_id)
    await bot.send_video(
        chat_id=call.message.chat.id,
        video=file_id,
        reply_markup=cancel_media_keyboard()
    )


async def edit_exercise_start(call, bot):
    await bot.send_message(
        call.message.chat.id,
        edit_exercise_category_msg,
        reply_markup=exercise_category_filter_keyboard()
    )


async def edit_exercise_handle_category(call, bot):
    category = call.data.split('_')[-1]
    await bot.edit_message_text(
        edit_exercise_difficulty_msg,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=exercise_difficulty_filter_keyboard(category)
    )


async def edit_exercise_show_list(call, bot):
    """
    Показывает список упражнений для редактирования с пагинацией.
    Может вызываться:
    - после выбора сложности(category, difficulty заданы)
    - при переходе по страницам (page меняется)
    - при закрытии упражнения
    - при удалении упражнения
    """
    if call.data.startswith('filter_edit_exercise_difficulty_'):
        page = 1
        category, difficulty = call.data.split('_')[4:]
    elif call.data.startswith('edit_exercise_back_to_list_'):
        page = 1
        category, difficulty = call.data.split('_')[5:]
    elif call.data.startswith('confirm_delete_ex_'):
        page = 1
        category, difficulty = call.data.split('_')[4:]
    else:
        page, category, difficulty = call.data.split('_')[3:]
    exercise_list = await get_exercises_id_name(category, difficulty)
    if exercise_list:
        text = exercises_list_header_msg
        keyboard = edit_ex_pagination_keyboard(exercise_list, category, difficulty, int(page))
    else:
        text = no_exercises_found_msg
        keyboard = no_exercises_keyboard()
    try:
        await bot.edit_message_text(text,
                                call.message.chat.id,
                                call.message.message_id,
                                reply_markup=keyboard
                                )
    except:
        await bot.send_message(call.message.chat.id,text,
                               reply_markup=keyboard)
    set_state(call.message.chat.id,'exercise_editing_menu',{
        'ui_context' : {
            'category':category,
            'difficulty':difficulty
        }
    }
              )


async def open_exercise_for_edit(bot, call=None, ex_id=None, message=None):
    """
    Открывает упражнение
    - из инлайн-кнопки.
    - при нажатии "Отмена" на этапе редактирования
    Отправляет сообщение с базовыми параметрами и инлайн-кнопками для редактирования.
    """
    if message:
        user_id = message.chat.id
        message_id = message.message_id
    else:
        user_id = call.message.chat.id
        message_id = call.message.message_id
    clear_state_keep_data(user_id)
    data = get_state(user_id)[-1]
    if not data or not data.get("ui_context"):
        await bot.send_message(user_id,exercise_edit_error_msg)
        return
    data = data["ui_context"]
    old_category, old_difficulty = data['category'], data['difficulty']
    exercise_id = ex_id or int(call.data.split('_')[-1])
    exercise_info = await get_exercise_by_id(exercise_id)
    (ex_id, name, description, category, difficulty, file_id, created_by,
     created_at, updated_at, is_active) = exercise_info
    try:
            await bot.delete_message(user_id, message_id)
    except:
        pass
    await bot.send_message(
        user_id,
        exercise_full_details_msg(ex_id, name, description, category,
                                  difficulty, created_by, created_at,
                                  is_active),
        reply_markup=exercise_edit_keyboard(ex_id, old_category, old_difficulty)
    )


async def handle_exercise_edit(call, bot):
    user_id = call.message.chat.id
    ex_id, action = call.data.split('_')[3:]
    data = get_state(user_id)[-1]
    if not data or not data.get("ui_context"):
        await bot.send_message(user_id, exercise_edit_error_msg)
        return
    match action:
        case 'name':
            text = edit_exercise_field_name_msg
            keyboard = exercise_edit_cancel_keyboard(ex_id)
        case 'desc':
            text = edit_exercise_field_description_msg
            keyboard = exercise_edit_cancel_keyboard(ex_id)
        case 'cat':
            text = edit_exercise_field_category_msg
            keyboard = ex_category_keyboard(mode='edit', ex_id=ex_id)
        case 'diff':
            text = edit_exercise_field_difficulty_msg
            keyboard = ex_difficulty_keyboard(mode='edit', ex_id=ex_id)
        case 'videochange':
            text = edit_exercise_field_video_msg
            keyboard = exercise_edit_cancel_keyboard(ex_id)
        case 'status':
            now_status = await get_exercise_status(ex_id)
            new_status = 0 if now_status else 1
            await update_exercise_in_db(ex_id, 'is_active', new_status)
            await open_exercise_for_edit(call=call, bot=bot, ex_id=ex_id)
            return
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    sent_msg = await bot.send_message(user_id, text, reply_markup=keyboard)
    state,data = get_state(user_id)
    data['ex_id'] = ex_id
    data['action'] = action
    data['prompt_msg_id'] = sent_msg.message_id
    set_state(user_id, 'waiting_new_exercise_field', data
              )


async def save_exercise_changes(bot, message=None, call=None):
    if message:
        user_id = message.chat.id
        message_id = message.message_id
    else:
        user_id = call.message.chat.id
        message_id = call.message.message_id
    state, data = get_state(user_id)
    if state != 'waiting_new_exercise_field':
        await bot.send_message(user_id, error_msg)
        return
    ex_id = data['ex_id']
    action = data['action']
    if action == 'name':
        new_field = message.text
        if await is_exercise_name_exists(new_field):
            await bot.send_message(
                message.chat.id,
                exercise_name_exists,
                reply_markup=exercise_edit_cancel_keyboard(ex_id=ex_id)
            )
            return
        if len(new_field) > 50:
            await bot.send_message(message.chat.id,
                                   exercise_name_too_long_msg,
                                   reply_markup=exercise_edit_cancel_keyboard(ex_id=ex_id))
            return
        if not await censor_check(new_field):
            await removal_of_admin_rights(bot, new_field,
                                          message.chat.id,
                                          message.from_user.username,
                                          'exercise'
                                          )
            return


    elif action == 'desc':
        new_field = message.text
        if len(new_field) < 20:
            await bot.send_message(message.chat.id,
                                   exercise_description_too_short_msg,
                                   reply_markup=exercise_edit_cancel_keyboard(ex_id=ex_id))
            return

        if len(new_field) > 500:
            await bot.send_message(message.chat.id,
                                   exercise_description_too_long_msg,
                                   reply_markup=exercise_edit_cancel_keyboard(ex_id=ex_id))
            return
        if not await censor_check(new_field):
            await removal_of_admin_rights(bot, new_field,
                                          message.chat.id,
                                          message.from_user.username,
                                          'exercise'
                                          )
            return
    elif action == 'cat':
        new_field = call.data.split('_')[-1]
    elif action == 'diff':
        new_field = call.data.split('_')[-1]
    elif action == 'videochange':
        new_field = message.video.file_id if message.video else message.animation.file_id
    else:
        return
    field_mapping = {
        'name': 'name',
        'desc': 'description',
        'cat': 'category',
        'diff': 'difficulty',
        'videochange': 'file_id',
    }
    db_field = field_mapping.get(action)
    await update_exercise_in_db(ex_id, db_field, new_field)
    prompt_msg_id = data.get('prompt_msg_id')
    try:
        if prompt_msg_id:
            await bot.delete_message(user_id, prompt_msg_id)
    except:
        pass
    if call:
        await open_exercise_for_edit(bot, call=call, ex_id=ex_id)
    else:
        await open_exercise_for_edit(bot, message=message, ex_id=ex_id)
async def accept_delete_exercise(call,bot):
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    ex_id,category,difficulty = call.data.split('_')[3:]
    await bot.send_message(
        call.message.chat.id,
        confirm_delete_exercise_msg(ex_id),
        reply_markup=ex_confirm_delete_keyboard(ex_id,category,difficulty)
    )
async def delete_exercise(call,bot):
    await bot.answer_callback_query(call.id,exercise_deleted_msg)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    ex_id,category,difficulty = call.data.split('_')[3:]
    await delete_exercise_in_db(ex_id)
    data = get_state(call.message.chat.id)[-1]
    if not data or not data.get("ui_context"):
        await exercise_management(call.message,bot,call.from_user.first_name)
        return
    await edit_exercise_show_list(call,bot)
async def cancel_delete_exercise(call,bot):
    await bot.answer_callback_query(call.id,cancellation)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    data = get_state(call.message.chat.id)[-1]
    if not data or not data.get("ui_context"):
        await exercise_management(call.message,bot,call.from_user.first_name)
        return
    ex_id = call.data.split('_')[-3]
    await open_exercise_for_edit(bot,call=call,ex_id=ex_id)

async def stats_exercise(call,bot):
    stats = await get_exercise_stats()
    await bot.send_message(
        call.message.chat.id,
        exercise_stats_msg(stats),
        reply_markup=cancel_any_keyboard()
    )
