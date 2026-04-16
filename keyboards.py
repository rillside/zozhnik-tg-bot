from telebot import types

from config import is_owner
from handlers.support.ticket_sorting import sort_ticket


# Основное меню

def timezone_selection_keyboard() -> types.InlineKeyboardMarkup:
    """Инлайн клавиатура выбора часового пояса."""
    keyboard = types.InlineKeyboardMarkup()
    timezone_first = types.InlineKeyboardButton('🏰 Калининград', callback_data='timezone_-1')
    timezone_second = types.InlineKeyboardButton('⭐ Москва', callback_data='timezone_0')
    timezone_third = types.InlineKeyboardButton('🌉 Самара', callback_data='timezone_1')
    timezone_fourth = types.InlineKeyboardButton('🏔️ Екатеринбург', callback_data='timezone_2')
    timezone_fifth = types.InlineKeyboardButton('🌾 Омск', callback_data='timezone_3')
    timezone_sixth = types.InlineKeyboardButton('⛰️ Красноярск', callback_data='timezone_4')
    timezone_seventh = types.InlineKeyboardButton('🏞️ Иркутск', callback_data='timezone_5')
    timezone_eighth = types.InlineKeyboardButton('❄️ Якутск', callback_data='timezone_6')
    timezone_ninth = types.InlineKeyboardButton('🌅 Владивосток', callback_data='timezone_7')
    timezone_tenth = types.InlineKeyboardButton('🏝️ Магадан', callback_data='timezone_8')
    timezone_eleventh = types.InlineKeyboardButton('🌋 Камчатка', callback_data='timezone_9')
    keyboard.add(timezone_first, timezone_second, timezone_third,
                 timezone_fourth, timezone_fifth, timezone_sixth,
                 timezone_seventh, timezone_eighth, timezone_ninth,
                 timezone_tenth, timezone_eleventh)
    return keyboard


def main_menu(user_id: int, is_admin: bool) -> types.ReplyKeyboardMarkup:
    """Основная реплай-клавиатура для пользователя."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("💧 Водный баланс")
    keyboard.add("💪 Физ-активность", "😴 Сон")
    keyboard.add("📊 Статистика", "⚙️ Настройки")
    if is_admin:
        keyboard.add("👨‍⚕️ Персональный специалист",
                     "🛠️ Админ панель")
    else:
        keyboard.add("👨‍⚕️ Персональный специалист")
    return keyboard


def admin_menu(id: int) -> types.ReplyKeyboardMarkup:
    """Основная клавиатура администрации."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📊 Статистика пользователей", "📢 Рассылка")
    keyboard.add("💪 Управление упражнениями", "👨‍⚕️ Обращения")
    keyboard.add("🔍 Пользователи")
    if is_owner(id):
        keyboard.add("👑 Управление администрацией")
    keyboard.add("↩️ На главную")

    return keyboard


def owner_menu(admins: list) -> types.InlineKeyboardMarkup:
    """Клавиатура для владельца с управлением администрацией."""
    keyboard = types.InlineKeyboardMarkup()
    btn_add = types.InlineKeyboardButton("⚡ Добавить администратора", callback_data='add_adm')
    keyboard.add(btn_add)
    if admins:
        btn_remove = types.InlineKeyboardButton("🚫 Удалить администратора", callback_data='remove_adm')
        keyboard.add(btn_remove)
    return keyboard


def own_cancel() -> types.InlineKeyboardMarkup:
    """Кнопка отмены для операций владельца."""
    keyboard = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data='own_cancel')
    keyboard.add(btn_cancel)
    return keyboard


def cancel_br_start() -> types.InlineKeyboardMarkup:
    """Кнопка отмены начала рассылки."""
    keyboard = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data='br_start_cancel')
    keyboard.add(btn_cancel)
    return keyboard


def return_admin_rights() -> types.InlineKeyboardMarkup:
    """Кнопка восстановления прав администратора."""
    keyboard = types.InlineKeyboardMarkup()
    btn_return_adm = types.InlineKeyboardButton("🔓 Восстановить права", callback_data='return_adm')
    keyboard.add(btn_return_adm)
    return keyboard


def accept_send(type_broadcast: str = 'msg') -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения или отмены рассылки."""
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Отправить рассылку", callback_data=f'br_accept_{type_broadcast}')
    btn_cancel = types.InlineKeyboardButton("❌ Отменить отправку", callback_data=f'br_cancel')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


# Настройки

def settings_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура раздела настроек."""
    keyboard = types.InlineKeyboardMarkup()
    water_settings = types.InlineKeyboardButton("💧 Вода", callback_data='water_settings')
    activity_settings = types.InlineKeyboardButton("💪 Активность", callback_data='activity_settings')
    dream_settings = types.InlineKeyboardButton("😴 Сон", callback_data='dream_settings')
    timezone_settings = types.InlineKeyboardButton("🌍 Часовой пояс", callback_data='timezone_settings')
    review_settings = types.InlineKeyboardButton("📈 Обзор", callback_data='review_settings')
    cancel_settings = types.InlineKeyboardButton("↩️ Закрыть настройки", callback_data='cancel_settings')
    keyboard.add(water_settings, activity_settings, dream_settings)
    keyboard.add(timezone_settings, review_settings)
    keyboard.add(cancel_settings)
    return keyboard


# Водный трекер

def water_goal_not_set_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка настройки трекера, если цель по воде не установлена."""
    keyboard = types.InlineKeyboardMarkup()
    go_to_water_stg = types.InlineKeyboardButton('⚙️ Настроить', callback_data='water_settings')
    keyboard.add(go_to_water_stg)
    return keyboard


def water_setup_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора параметра водного трекера."""
    keyboard = types.InlineKeyboardMarkup()
    water_target = types.InlineKeyboardButton("🎯 Цель на день", callback_data='water_goal')
    water_reminder = types.InlineKeyboardButton("⏰ Напоминания", callback_data='water_reminder')
    water_exit = types.InlineKeyboardButton("🚶 Назад", callback_data='water_stg_cancel')
    keyboard.add(water_target, water_reminder, water_exit)
    return keyboard


def water_goal_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора дневной цели по воде."""
    keyboard = types.InlineKeyboardMarkup()
    water_goal_first = types.InlineKeyboardButton("💧 1.5л", callback_data='water_goal_1500')
    water_goal_second = types.InlineKeyboardButton("💧 2.0л", callback_data='water_goal_2000')
    water_goal_third = types.InlineKeyboardButton("💧 2.5л", callback_data='water_goal_2500')
    water_goal_fourth = types.InlineKeyboardButton("💧 3.0л", callback_data='water_goal_3000')
    water_goal_custom = types.InlineKeyboardButton("💧 Своя цель", callback_data='water_goal_custom')
    water_goal_exit = types.InlineKeyboardButton("↩️ Назад", callback_data='water_goal_exit')
    keyboard.add(water_goal_first, water_goal_second,
                 water_goal_third, water_goal_fourth, water_goal_custom, water_goal_exit)
    return keyboard


def water_goal_custom_cancel() -> types.InlineKeyboardMarkup:
    """Кнопка отмены ввода произвольной цели по воде."""
    keyboard = types.InlineKeyboardMarkup()
    water_exit = types.InlineKeyboardButton("❌ Отмена", callback_data='water_goal_custom_cancel')
    keyboard.add(water_exit)
    return keyboard


def get_water_reminder_type_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора типа напоминаний о воде."""
    keyboard = types.InlineKeyboardMarkup()
    type_interval = types.InlineKeyboardButton("⏰ По интервалу", callback_data='type_interval')
    type_smart = types.InlineKeyboardButton("🤖 Умный режим", callback_data='type_smart')
    water_reminder_type_cancel = types.InlineKeyboardButton("🔙 Назад", callback_data='water_reminder_exit')
    keyboard.add(type_interval, type_smart, water_reminder_type_cancel)
    return keyboard


# Физическая активность

def activity_setup_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора параметра трекера активности."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🎯 Цель на день", callback_data='activity_goal'),
        types.InlineKeyboardButton("⏰ Напоминания", callback_data='activity_reminder')
    )
    keyboard.add(types.InlineKeyboardButton("🚶 Назад", callback_data='activity_stg_cancel'))
    return keyboard


def activity_goal_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора дневной цели по активности."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("1", callback_data='activity_goal_1'),
        types.InlineKeyboardButton("3", callback_data='activity_goal_3'),
        types.InlineKeyboardButton("5", callback_data='activity_goal_5'),
        types.InlineKeyboardButton("10", callback_data='activity_goal_10')
    )
    keyboard.add(
        types.InlineKeyboardButton("✏️ Своя цель", callback_data='activity_goal_custom'),
        types.InlineKeyboardButton("↩️ Назад", callback_data='activity_goal_exit')
    )
    return keyboard


def activity_goal_custom_cancel() -> types.InlineKeyboardMarkup:
    """Кнопка отмены ввода произвольной цели по активности."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("❌ Отмена", callback_data='activity_goal_custom_cancel'))
    return keyboard


def activity_goal_not_set_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка настройки трекера, если цель по активности не установлена."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('⚙️ Настроить', callback_data='activity_settings'))
    return keyboard


def activity_reminder_type_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора типа напоминаний об активности."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("⏰ По интервалу", callback_data='activity_type_interval'),
        types.InlineKeyboardButton("🤖 Умный режим", callback_data='activity_type_smart')
    )
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data='activity_reminder_exit'))
    return keyboard


def activity_interval_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора интервала напоминаний об активности."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("1ч", callback_data='activity_interval_1'),
        types.InlineKeyboardButton("2ч", callback_data='activity_interval_2'),
        types.InlineKeyboardButton("3ч", callback_data='activity_interval_3'),
        types.InlineKeyboardButton("4ч", callback_data='activity_interval_4'),
        types.InlineKeyboardButton("5ч", callback_data='activity_interval_5')
    )
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data='activity_interval_exit'))
    return keyboard


def get_water_interval_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора интервала напоминаний о воде."""
    keyboard = types.InlineKeyboardMarkup()
    water_interval_1h = types.InlineKeyboardButton("1️⃣ 1ч", callback_data='water_interval_1h')
    water_interval_2h = types.InlineKeyboardButton("2️⃣ 2ч", callback_data='water_interval_2h')
    water_interval_3h = types.InlineKeyboardButton("3️⃣ 3ч", callback_data='water_interval_3h')
    water_interval_4h = types.InlineKeyboardButton("4️⃣ 4ч", callback_data='water_interval_4h')
    water_interval_5h = types.InlineKeyboardButton("5️⃣ 5ч", callback_data='water_interval_5h')
    water_interval_exit = types.InlineKeyboardButton("🔙 Назад", callback_data='water_interval_exit')
    keyboard.add(water_interval_1h, water_interval_2h, water_interval_3h, water_interval_4h, water_interval_5h,
                 water_interval_exit)
    return keyboard


def water_add_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура быстрого добавления воды."""
    keyboard = types.InlineKeyboardMarkup()
    water_add_250 = types.InlineKeyboardButton("🥛 250 мл.", callback_data='water_add_250')
    water_add_330 = types.InlineKeyboardButton("🥤 330 мл.", callback_data='water_add_330')
    water_add_450 = types.InlineKeyboardButton("💧 450 мл.", callback_data='water_add_450')
    water_add_750 = types.InlineKeyboardButton("🫖 750 мл.", callback_data='water_add_750')
    water_add_1000 = types.InlineKeyboardButton("🪣 1000 мл.", callback_data='water_add_1000')
    water_add_custom = types.InlineKeyboardButton("✏️ Свой объём", callback_data='water_add_custom')
    water_goal_exit = types.InlineKeyboardButton("↩️ Назад", callback_data='water_add_exit')
    keyboard.add(water_add_250, water_add_330, water_add_450, water_add_750, water_add_1000, water_add_custom,
                 water_goal_exit)
    return keyboard


# Поддержка

def support_selection_keyboard() -> types.InlineKeyboardMarkup:
    """Главная клавиатура раздела поддержки."""
    keyboard = types.InlineKeyboardMarkup()
    technical_support = types.InlineKeyboardButton("🔧 Техподдержка", callback_data='technical_support')
    personal_consultation = types.InlineKeyboardButton("👨‍⚕️ Консультация", callback_data='personal_consultation')
    my_tickets = types.InlineKeyboardButton("📋 Мои обращения", callback_data='my_tickets')
    supp_exit = types.InlineKeyboardButton("🔙  Выйти", callback_data='back_to_main')
    keyboard.add(technical_support, personal_consultation,
                 my_tickets, supp_exit)
    return keyboard


def technical_support_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура открытия обращения в техподдержку."""
    keyboard = types.InlineKeyboardMarkup()
    tech_supp_open_ticket = types.InlineKeyboardButton("📨 Открыть обращение", callback_data='tech_supp_open_ticket')
    supp_cancel_opening = types.InlineKeyboardButton("🚫 Отмена", callback_data='supp_cancel_opening')
    keyboard.add(tech_supp_open_ticket, supp_cancel_opening)
    return keyboard


def consultation_support_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура открытия обращения за консультацией."""
    keyboard = types.InlineKeyboardMarkup()
    tech_supp_open_ticket = types.InlineKeyboardButton("📨 Открыть обращение", callback_data='consult_supp_open_ticket')
    supp_cancel_opening = types.InlineKeyboardButton("🚫 Отмена", callback_data='supp_cancel_opening')
    keyboard.add(tech_supp_open_ticket, supp_cancel_opening)
    return keyboard


def supp_ticket_cancel_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка отмены при создании тикета."""
    keyboard = types.InlineKeyboardMarkup()
    supp_ticket_exit = types.InlineKeyboardButton("❌ Отмена", callback_data='supp_ticket_exit')
    keyboard.add(supp_ticket_exit)
    return keyboard


def supp_ticket_draft_keyboard(id_ticket: int) -> types.InlineKeyboardMarkup:
    """Клавиатура для черновика тикета: перейти в диалог или удалить."""
    keyboard = types.InlineKeyboardMarkup()
    go_to_chat = types.InlineKeyboardButton("💬 К диалогу",
                                            callback_data=f'accept_ticket_{id_ticket}')
    delete = types.InlineKeyboardButton("🚫 Удалить",
                                        callback_data=f'delete_ticket_{id_ticket}')
    keyboard.add(go_to_chat, delete)
    return keyboard


def go_to_ticket_keyboard(ticket_id: int, role: str) -> types.InlineKeyboardMarkup:
    """Кнопка открытия конкретного тикета."""
    keyboard = types.InlineKeyboardMarkup()
    open_ticket = types.InlineKeyboardButton("📨 Открыть обращение", callback_data=f'open_ticket_{ticket_id}_{role}')
    keyboard.add(open_ticket)
    return keyboard


def opening_ticket_keyboard(role: str, ticket_info: tuple, page: int = 1) -> types.InlineKeyboardMarkup:
    """Клавиатура со списком тикетов с пагинацией."""
    type = ticket_info[0]
    ticket_list = ticket_info[1]
    ticket_list.sort(key=sort_ticket)
    count_ticket = len(ticket_list)
    total_page = -(-count_ticket // 10)  # Округление вверх
    first_ticket_in_page = page * 10 - 10
    last_ticket_in_page = page * 10 + 1
    keyboard = types.InlineKeyboardMarkup()
    for i in ticket_list[first_ticket_in_page:last_ticket_in_page]:
        status = i.get('status_for_user') or i.get('status_for_admin')
        emoji = '\U0001F195' if status == 'new' else None
        keyboard.row(
            types.InlineKeyboardButton(
                f"{emoji if emoji else ''} {i.get('title', '')}",
                callback_data=f"open_ticket_{i.get('id')}_{role}"))
    page_management_buttons = []
    if page > 1:
        page_management_buttons.append(
            types.InlineKeyboardButton(
                '⬅️ Назад', callback_data=f'tickets_page_{page - 1}_{role}' + (f'_{type}' if role == 'admin' and type else ''))
        )
    else:
        page_management_buttons.append(types.InlineKeyboardButton("🔙  Выйти", callback_data=f'tickets_exit_{role}'))
    page_management_buttons.append(types.InlineKeyboardButton(
        f'📄 {page}/{total_page}', callback_data='info_page')
    )
    if total_page > page:
        page_management_buttons.append(types.InlineKeyboardButton(
            "▶️ Вперед", callback_data=f"tickets_page_{page + 1}_{role}" + (f"_{type}" if role == 'admin' and type else ""))
        )
    keyboard.row(*page_management_buttons)
    return keyboard


def ticket_actions_keyboard(messages_id: list | None = None, role: str = 'user', type: str | None = None, id_ticket: int | None = None, photos_id: list | None = None) -> types.InlineKeyboardMarkup:
    """Клавиатура действий внутри открытого тикета."""
    data = ''
    if messages_id:
        for i in messages_id:
            data += f"_{i.message_id}"
    keyboard = types.InlineKeyboardMarkup()
    main_buttons = [
        types.InlineKeyboardButton('⬅️ Закрыть', callback_data=f'ticket_exit{data}_{role}{'_' + type if type else ''}')]
    if role == 'user':
        main_buttons.append(
            types.InlineKeyboardButton('🗑️ Удалить обращение', callback_data=f'confirm_delete_ticket_{id_ticket}'))
    keyboard.row(*main_buttons)
    if photos_id:
        photo_buttons = []
        for num, photo_id in enumerate(photos_id):
            photo_buttons.append(
                types.InlineKeyboardButton(f'📷 Фото №{num + 1}', callback_data=f'opening_photo_{photo_id}'))
        keyboard.row(*photo_buttons)
    return keyboard


def cancel_media_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка закрытия просматриваемого медиафайла."""
    keyboard = types.InlineKeyboardMarkup()
    cancel_btn = types.InlineKeyboardButton('⬅️ Закрыть', callback_data='cancel_media')
    keyboard.add(cancel_btn)
    return keyboard


def admin_ticket_section_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора раздела тикетов для администратора."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔧 Техподдержка", callback_data="adm_tickets_tech"),
        types.InlineKeyboardButton("👨‍⚕️ Консультации", callback_data="adm_tickets_consult"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="adm_back_main")
    )

    return keyboard


def accept_aggressive_title_keyboard(title: str, type_ticket: str) -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения заголовка тикета, помеченного как агрессивный."""
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить",
                                            callback_data=f'aggressive_title_accept_{title}_{type_ticket}')
    btn_cancel = types.InlineKeyboardButton("❌ Отменить", callback_data=f'aggressive_title_cancel')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


def accept_aggressive_msg_keyboard(ticket_id: int, text: str) -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения сообщения в тикете, помеченного как агрессивное."""
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить отправку",
                                            callback_data=f'aggressive_msg_to_ticket_accept_{ticket_id}_{text}')
    btn_cancel = types.InlineKeyboardButton("❌ Отменить отправку",
                                            callback_data=f'aggressive_msg_to_ticket_cancel_{ticket_id}')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


def accept_custom_add_water_keyboard(amount_ml: int) -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения произвольного объёма воды."""
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'water_add_{amount_ml}')
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=f'water_add_custom_cancel')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


def cancel_custom_add_water_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка отмены ввода произвольного объёма воды."""
    keyboard = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=f'water_add_custom_cancel')
    keyboard.add(btn_cancel)
    return keyboard


def accept_delete_ticket_keyboard(ticket_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления тикета."""
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'delete_ticket_{ticket_id}')
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=f'cancel_delete_ticket_{ticket_id}')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


# Упражнения (администрирование)

def admin_exercise_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура управления упражнениями для администратора."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton("📝 Добавить", callback_data="admin_exercise_add"),
        types.InlineKeyboardButton("✏️ Редактировать", callback_data="admin_exercise_edit"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="admin_exercise_stats"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="admin_back_main")
    ]

    keyboard.add(*buttons)
    return keyboard


def exercise_navigation_keyboard(step: int) -> types.InlineKeyboardMarkup:
    """Клавиатура навигации при пошаговом добавлении упражнения."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    if step > 1:
        buttons.append(types.InlineKeyboardButton("🔙 Назад", callback_data="add_exercise_back"))
    # На шаге добавления видео даём возможность пропустить его
    if step == 5:
        buttons.append(types.InlineKeyboardButton("⏭️ Пропустить", callback_data="add_exercise_skip_video"))
    buttons.append(types.InlineKeyboardButton("❌ Отмена", callback_data="add_exercise_cancel"))
    keyboard.row(*buttons)
    return keyboard



def ex_category_keyboard(mode: str = 'add', ex_id: int | None = None) -> types.InlineKeyboardMarkup:
    """Клавиатура выбора категории упражнения."""

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("💪 Силовые", callback_data=f"{mode}_exercise_category_strength"),
        types.InlineKeyboardButton("🏃 Кардио", callback_data=f"{mode}_exercise_category_cardio")
    )
    keyboard.add(
        types.InlineKeyboardButton("🧘 Растяжка", callback_data=f"{mode}_exercise_category_stretching"),
        types.InlineKeyboardButton("🚶 Ходьба", callback_data=f"{mode}_exercise_category_walking")
    )
    keyboard.add(
        types.InlineKeyboardButton("🧍 Зарядка", callback_data=f"{mode}_exercise_category_warmup"),
        types.InlineKeyboardButton("⚖️ Баланс", callback_data=f"{mode}_exercise_category_balance")
    )
    if mode == 'add':
        keyboard.add(
            types.InlineKeyboardButton("🔙 Назад", callback_data="add_exercise_back"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="add_exercise_cancel")
        )
    else:
        keyboard.add(
            types.InlineKeyboardButton("❌ Отмена",callback_data=f"edit_exercise_select_{ex_id}"),
        )

    return keyboard


def ex_difficulty_keyboard(mode: str = 'add', ex_id: int | None = None) -> types.InlineKeyboardMarkup:
    """Клавиатура выбора уровня сложности упражнения."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(types.InlineKeyboardButton("🌱 Новичок", callback_data=f"{mode}_exercise_difficulty_beginner"))
    keyboard.add(types.InlineKeyboardButton("🌿 Средний", callback_data=f"{mode}_exercise_difficulty_intermediate"))
    keyboard.add(types.InlineKeyboardButton("🌳 Продвинутый", callback_data=f"{mode}_exercise_difficulty_advanced"))
    if mode == 'add':
        keyboard.add(
            types.InlineKeyboardButton("🔙 Назад", callback_data="add_exercise_back"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="add_exercise_cancel")
        )
    else:
        keyboard.add(
            types.InlineKeyboardButton("❌ Отмена", callback_data=f"edit_exercise_select_{ex_id}"),
        )

    return keyboard

def exercise_confirm_keyboard(has_video: bool = True) -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения или отмены добавления упражнения."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    if has_video:
        keyboard.add(types.InlineKeyboardButton('📷 Открыть видео', callback_data="exercise_confirm_open_video"))
    keyboard.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data="exercise_confirm_save"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="add_exercise_cancel")
    )
    return keyboard
    return keyboard
def exercise_category_filter_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора категории для фильтрации при редактировании упражнений."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("💪 Силовые", callback_data="filter_edit_exercise_category_strength"),
        types.InlineKeyboardButton("🏃 Кардио", callback_data="filter_edit_exercise_category_cardio")
    )
    keyboard.add(
        types.InlineKeyboardButton("🧘 Растяжка", callback_data="filter_edit_exercise_category_stretching"),
        types.InlineKeyboardButton("🚶 Ходьба", callback_data="filter_edit_exercise_category_walking")
    )
    keyboard.add(
        types.InlineKeyboardButton("🧍 Зарядка", callback_data="filter_edit_exercise_category_warmup"),
        types.InlineKeyboardButton("⚖️ Баланс", callback_data="filter_edit_exercise_category_balance")
    )

    keyboard.add(
        types.InlineKeyboardButton("❌ Отмена", callback_data="edit_exercise_cancel")
    )

    return keyboard
def exercise_difficulty_filter_keyboard(category: str) -> types.InlineKeyboardMarkup:
    """Клавиатура выбора уровня сложности при фильтрации упражнений для редактирования."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton("🌱 Новичок", callback_data=f"filter_edit_exercise_difficulty_{category}_beginner"),
        types.InlineKeyboardButton("🌿 Средний", callback_data=f"filter_edit_exercise_difficulty_{category}_intermediate"),
        types.InlineKeyboardButton("🌳 Продвинутый", callback_data=f"filter_edit_exercise_difficulty_{category}_advanced")
    )

    keyboard.add(
        types.InlineKeyboardButton("🔙 Назад к категориям", callback_data="edit_exercise_back_to_categories"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="edit_exercise_cancel")
    )

    return keyboard
def edit_ex_pagination_keyboard(exercise_list: list, category: str, difficulty: str, page: int = 1) -> types.InlineKeyboardMarkup:
    """Клавиатура списка упражнений с пагинацией для режима редактирования."""
    exercise_list.reverse()
    total_pages = -(-len(exercise_list)//10) # к большему
    first = page * 10 - 10
    last = page * 10 + 1
    keyboard = types.InlineKeyboardMarkup()
    for ex_id,name in exercise_list[first:last]:
        keyboard.row(
            types.InlineKeyboardButton(f"📋 {name}",callback_data=f"edit_exercise_select_{ex_id}")
        )
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"edit_exercises_page_{page - 1}_{category}_{difficulty}"
        ))
    else:
        nav_buttons.append(types.InlineKeyboardButton("🔙  Выйти", callback_data='edit_exercise_cancel'))

    nav_buttons.append(types.InlineKeyboardButton(
        f"{page}/{total_pages}",
        callback_data="edit_exercises_page_info"
    ))

    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton(
            "➡️ Вперед",
            callback_data=f"edit_exercises_page_{page + 1}_{category}_{difficulty}"
        ))

    keyboard.row(*nav_buttons)
    return keyboard

def no_exercises_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура, отображаемая когда в категории нет упражнений для редактирования."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔄 Выбрать другую категорию", callback_data="edit_exercise_back_to_categories"),
        types.InlineKeyboardButton("➕ Создать упражнение", callback_data="admin_exercise_add"),
        types.InlineKeyboardButton("❌ Выйти", callback_data="edit_exercise_cancel")
    )

    return keyboard


# Клавиатуры бота

def exercise_edit_keyboard(exercise_id: int, category: str, difficulty: str, has_video: bool = False) -> types.InlineKeyboardMarkup:
    """Клавиатура редактирования полей конкретного упражнения."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # Кнопки для редактирования каждого параметра
    keyboard.add(
        types.InlineKeyboardButton("📝 Название", callback_data=f"ex_edit_field_{exercise_id}_name"),
        types.InlineKeyboardButton("📋 Описание", callback_data=f"ex_edit_field_{exercise_id}_desc")
    )
    keyboard.add(
        types.InlineKeyboardButton("🏷️ Категория", callback_data=f"ex_edit_field_{exercise_id}_cat"),
        types.InlineKeyboardButton("📊 Сложность", callback_data=f"ex_edit_field_{exercise_id}_diff")
    )

    # Кнопки для видео
    if has_video:
        keyboard.row(
            types.InlineKeyboardButton("📹 Открыть видео", callback_data=f"ex_edit_open_video_{exercise_id}"),
            types.InlineKeyboardButton("📹 Заменить видео", callback_data=f"ex_edit_field_{exercise_id}_videochange")
        )
    else:
        # Если видео нет, показываем только замену (добавление)
        keyboard.row(
            types.InlineKeyboardButton("📹 Добавить видео", callback_data=f"ex_edit_field_{exercise_id}_videochange")
        )

    # Кнопки статуса и удаления
    keyboard.add(
        types.InlineKeyboardButton("🔄 Изменить статус", callback_data=f"ex_edit_field_{exercise_id}_status"),
        types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"ex_edit_delete_{exercise_id}_{category}_{difficulty}")
    )

    # Навигация
    keyboard.add(
        types.InlineKeyboardButton("🔙 К списку", callback_data=f"edit_exercise_back_to_list_{category}_{difficulty}"),
        types.InlineKeyboardButton("❌ Выйти", callback_data="edit_exercise_cancel")
    )

    return keyboard
def exercise_edit_cancel_keyboard(ex_id: int) -> types.InlineKeyboardMarkup:
    """Кнопка отмены редактирования поля упражнения."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('❌ Отмена',callback_data=f"edit_exercise_select_{ex_id}")
    )
    return keyboard


def ex_confirm_delete_keyboard(ex_id: int, category: str, difficulty: str) -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления упражнения."""
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton("✅ Удалить", callback_data=f"confirm_delete_ex_{ex_id}_{category}_{difficulty}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_delete_ex_{ex_id}_{category}_{difficulty}")
    )

    return keyboard
def cancel_any_keyboard() -> types.InlineKeyboardMarkup:
    """Универсальная кнопка закрытия текущего сообщения."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('⬅️ Закрыть', callback_data='cancel_any')
    )
    return keyboard


def stats_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура под сообщением со статистикой."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('🏆 Таблица лидеров', callback_data='leaderboard_open'),
        types.InlineKeyboardButton('🎮 Мой XP', callback_data='xp_profile'),
    )
    keyboard.add(
        types.InlineKeyboardButton('🤖 ИИ-анализ профиля', callback_data='ai_analyze')
    )
    keyboard.add(
        types.InlineKeyboardButton('⬅️ Закрыть', callback_data='cancel_any')
    )
    return keyboard


# Трекер сна

def sleep_not_set_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка перехода к настройке трекера сна, если он не настроен."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('⚙️ Настроить', callback_data='dream_settings'))
    return keyboard


def sleep_setup_keyboard(reminders_enabled: bool = True) -> types.InlineKeyboardMarkup:
    """Клавиатура настроек трекера сна: время отбоя/подъёма и переключение напоминаний."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🌙 Время отбоя", callback_data='sleep_stg_sleep_time'),
        types.InlineKeyboardButton("☀️ Время подъёма", callback_data='sleep_stg_wake_time'),
    )
    keyboard.add(
        types.InlineKeyboardButton(
            f"🔔 Напоминания: {'вкл ✅' if reminders_enabled else 'выкл ❌'}",
            callback_data='sleep_stg_toggle_reminder'
        )
    )
    keyboard.add(types.InlineKeyboardButton("🚶 Назад", callback_data='sleep_stg_cancel'))
    return keyboard


def sleep_time_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора времени отбоя."""
    keyboard = types.InlineKeyboardMarkup()
    times = ['20:00', '21:00', '22:00', '23:00', '00:00', '01:00']
    row = []
    for t in times:
        row.append(types.InlineKeyboardButton(t, callback_data=f'select_sleep_time_{t}'))
        if len(row) == 3:
            keyboard.row(*row)
            row = []
    if row:
        keyboard.row(*row)
    keyboard.add(
        types.InlineKeyboardButton("✏️ Своё время", callback_data='sleep_time_custom'),
        types.InlineKeyboardButton("↩️ Назад", callback_data='sleep_time_exit')
    )
    return keyboard


def wake_time_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора времени подъёма."""
    keyboard = types.InlineKeyboardMarkup()
    times = ['05:00', '06:00', '07:00', '08:00', '09:00', '10:00']
    row = []
    for t in times:
        row.append(types.InlineKeyboardButton(t, callback_data=f'select_wake_time_{t}'))
        if len(row) == 3:
            keyboard.row(*row)
            row = []
    if row:
        keyboard.row(*row)
    keyboard.add(
        types.InlineKeyboardButton("✏️ Своё время", callback_data='wake_time_custom'),
        types.InlineKeyboardButton("↩️ Назад", callback_data='wake_time_exit')
    )
    return keyboard


def sleep_dashboard_keyboard(is_sleeping: bool = False) -> types.InlineKeyboardMarkup:
    """Клавиатура дашборда сна: кнопка начала/окончания сна и история."""
    keyboard = types.InlineKeyboardMarkup()
    if is_sleeping:
        keyboard.add(types.InlineKeyboardButton("☀️ Проснулся!", callback_data='sleep_log_end'))
    else:
        keyboard.add(types.InlineKeyboardButton("😴 Ложусь спать", callback_data='sleep_log_start'))
    keyboard.add(
        types.InlineKeyboardButton("📋 История сна", callback_data='sleep_history'),
        types.InlineKeyboardButton("🔙 Закрыть", callback_data='cancel_any')
    )
    return keyboard


def sleep_bedtime_reminder_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура уведомления об отбое: кнопка «Ложусь спать»."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("😴 Ложусь спать", callback_data='sleep_log_start'))
    return keyboard


def sleep_wakeup_reminder_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура уведомления о подъёме: кнопка «Проснулся!»."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("☀️ Проснулся!", callback_data='sleep_log_end'))
    return keyboard

def sleep_history_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка закрытия истории сна."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(types.InlineKeyboardButton("🔙 Закрыть", callback_data='cancel_sleep_history'))
    return keyboard


def sleep_cancel_custom_keyboard() -> types.InlineKeyboardMarkup:
    """Кнопка отмены ввода произвольного времени сна."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("❌ Отмена", callback_data='sleep_custom_time_cancel'))
    return keyboard


# Упражнения (пользователь)

def sports_main_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Главная клавиатура раздела физической активности."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🏋️ Все упражнения", callback_data="sports_check_all"),
        types.InlineKeyboardButton("❤️ Избранное", callback_data="sports_check_favorites")
    )
    keyboard.add(
        types.InlineKeyboardButton("📊 Мой прогресс", callback_data="sports_check_my_stats")
    )
    keyboard.add(
        types.InlineKeyboardButton("🔙 На главную", callback_data="back_to_main")
    )

    return keyboard


def sports_category_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора категории для просмотра всех упражнений."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("💪 Силовые", callback_data="sports_category_strength"),
        types.InlineKeyboardButton("🏃 Кардио", callback_data="sports_category_cardio")
    )
    keyboard.add(
        types.InlineKeyboardButton("🧘 Растяжка", callback_data="sports_category_stretching"),
        types.InlineKeyboardButton("🚶 Ходьба", callback_data="sports_category_walking")
    )
    keyboard.add(
        types.InlineKeyboardButton("🧍 Зарядка", callback_data="sports_category_warmup"),
        types.InlineKeyboardButton("⚖️ Баланс", callback_data="sports_category_balance")
    )

    keyboard.add(
        types.InlineKeyboardButton("🔙 Назад", callback_data="sports_back_to_main"),
        types.InlineKeyboardButton("❌ Закрыть", callback_data="sports_close")
    )
    return keyboard
def sports_difficulty_keyboard(category: str) -> types.InlineKeyboardMarkup:
    """Клавиатура выбора уровня сложности для просмотра упражнений."""
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        types.InlineKeyboardButton("🌱 Новичок", callback_data=f"sports_difficulty_{category}_beginner"),
        types.InlineKeyboardButton("🌿 Средний", callback_data=f"sports_difficulty_{category}_intermediate"),
        types.InlineKeyboardButton("🌳 Продвинутый", callback_data=f"sports_difficulty_{category}_advanced")
    )

    keyboard.add(
        types.InlineKeyboardButton("🔙 Назад к категориям", callback_data="sports_back_to_categories"),
        types.InlineKeyboardButton("❌ Закрыть", callback_data="sports_close")
    )

    return keyboard
def sports_all_pagination_keyboard(exercise_list: list, category: str, difficulty: str, page: int = 1) -> types.InlineKeyboardMarkup:
    """Клавиатура со списком всех активных упражнений с пагинацией."""
    exercise_list.reverse() #Сначала новые
    total_pages = -(-len(exercise_list)//10) # к большему
    first = page * 10 - 10
    last = page * 10 + 1
    keyboard = types.InlineKeyboardMarkup()
    for ex_id,name in exercise_list[first:last]:
        keyboard.row(
            types.InlineKeyboardButton(f"📋 {name}",callback_data=f"sports_open_ex_{ex_id}")
        )
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"sport_ex_all_page_{page - 1}_{category}_{difficulty}"
        ))
    else:
        nav_buttons.append(types.InlineKeyboardButton("🔙  Выйти", callback_data='sports_close'))

    nav_buttons.append(types.InlineKeyboardButton(
        f"{page}/{total_pages}",
        callback_data="ex_page_info"
    ))

    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton(
            "➡️ Вперед",
            callback_data=f"sport_ex_all_page_{page + 1}_{category}_{difficulty}"
        ))

    keyboard.row(*nav_buttons)
    return keyboard


def sports_favorites_pagination_keyboard(exercise_list: list, page: int = 1) -> types.InlineKeyboardMarkup:
    """Клавиатура списка избранных упражнений с пагинацией."""
    if not exercise_list:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="sports_back_to_main"))
        return keyboard
    total_pages = max(1, -(-len(exercise_list) // 10))
    first = (page - 1) * 10
    last = first + 10
    keyboard = types.InlineKeyboardMarkup()
    for ex_id, name in exercise_list[first:last]:
        keyboard.row(
            types.InlineKeyboardButton(f"📋 {name}", callback_data=f"sports_open_ex_{ex_id}")
        )
    nav_buttons = []
    if page > 1:
        nav_buttons.append(types.InlineKeyboardButton(
            "⬅️ Назад", callback_data=f"sport_ex_fav_page_{page - 1}"
        ))
    else:
        nav_buttons.append(types.InlineKeyboardButton("🔙 Выйти", callback_data="sports_back_to_main"))
    nav_buttons.append(types.InlineKeyboardButton(
        f"{page}/{total_pages}", callback_data="ex_page_info"
    ))
    if page < total_pages:
        nav_buttons.append(types.InlineKeyboardButton(
            "➡️ Вперед", callback_data=f"sport_ex_fav_page_{page + 1}"
        ))
    keyboard.row(*nav_buttons)
    return keyboard


def sports_favorites_empty_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура для пустого избранного."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔙 Назад", callback_data="sports_back_to_main"))
    return keyboard


def sports_confirm_done_keyboard(ex_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура подтверждения выполнения упражнения."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"sports_confirm_do_{ex_id}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data=f"sports_cancel_do_{ex_id}")
    )
    return keyboard


def sports_exercise_keyboard(exercise_id: int, is_favorite: bool, category: str, difficulty: str, has_video: bool = False) -> types.InlineKeyboardMarkup:
    """Клавиатура действий с конкретным упражнением для пользователя."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    # Основные действия
    # Основные действия
    main_buttons = [types.InlineKeyboardButton("✅ Выполнил", callback_data=f"sports_do_{exercise_id}")]
    if has_video:
        main_buttons.append(types.InlineKeyboardButton("📹 Видео", callback_data=f"ex_edit_open_video_{exercise_id}"))
    keyboard.add(*main_buttons)

    # Избранное
    fav_text = "❤️ Убрать" if is_favorite else "🤍 В избранное"
    keyboard.add(
        types.InlineKeyboardButton(fav_text, callback_data=f"sports_fav_{exercise_id}")
    )

    # Статистика и навигация
    keyboard.add(
        types.InlineKeyboardButton("📊 Статистика", callback_data=f"sports_my_stats_{exercise_id}"),
        types.InlineKeyboardButton("🔙 К списку", callback_data=f"sports_back_to_list_{category}_{difficulty}")
    )

    return keyboard


# Лидерборд и XP

def leaderboard_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура таблицы лидеров."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔄 Обновить", callback_data='leaderboard_refresh'))
    keyboard.add(types.InlineKeyboardButton("🎮 Мой профиль", callback_data='xp_profile'))
    keyboard.add(types.InlineKeyboardButton("⬅️ Статистика", callback_data='back_to_stats'))
    return keyboard


def xp_profile_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура профиля XP пользователя."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Статистика", callback_data='back_to_stats'))
    return keyboard


# Администрирование

def user_profile_admin_keyboard(user_id: int, status: str) -> types.InlineKeyboardMarkup:
    """Клавиатура просмотра и управления профилем пользователя для администратора."""
    keyboard = types.InlineKeyboardMarkup()
    if status == 'BANNED':
        keyboard.add(types.InlineKeyboardButton(
            "✅ Разбанить",
            callback_data=f'adm_unban_{user_id}'
        ))
    elif status not in ('Owner',):
        keyboard.add(types.InlineKeyboardButton(
            "🚫 Забанить",
            callback_data=f'adm_ban_{user_id}'
        ))
    keyboard.add(
        types.InlineKeyboardButton("➕ XP", callback_data=f'adm_xp_add_{user_id}'),
        types.InlineKeyboardButton("➖ XP", callback_data=f'adm_xp_sub_{user_id}')
    )
    keyboard.add(types.InlineKeyboardButton("🔙 Закрыть", callback_data='cancel_any'))
    return keyboard


def admin_search_cancel() -> types.InlineKeyboardMarkup:
    """Кнопка отмены поиска пользователя в панели администратора."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("❌ Отмена", callback_data='adm_search_cancel'))
    return keyboard


def admin_xp_cancel_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    """Кнопка отмены операции изменения XP пользователя."""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("❌ Отмена", callback_data=f'adm_xp_cancel_{user_id}'))
    return keyboard

