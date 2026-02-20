from telebot import types

from config import is_owner
from handlers.support.ticket_sorting import sort_ticket


def timezone_selection_keyboard():
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


def main_menu(user_id, is_admin):  # Основная клавиатура
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


def admin_menu(id):  # Основная Клавиатура администрации
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📊 Статистика пользователей", "📢 Рассылка")
    keyboard.add("💪 Управление упражнениями", "👨‍⚕️ Обращения")
    if is_owner(id):
        keyboard.add("👑 Управление администрацией")
    keyboard.add("↩️ На главную")

    return keyboard


def owner_menu(admins):  # Клавиатура Для владельцев
    keyboard = types.InlineKeyboardMarkup()
    btn_add = types.InlineKeyboardButton("⚡ Добавить администратора", callback_data='add_adm')
    keyboard.add(btn_add)
    if admins:
        btn_remove = types.InlineKeyboardButton("🚫 Удалить администратора", callback_data='remove_adm')
        keyboard.add(btn_remove)
    return keyboard


def own_cancel():
    keyboard = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data='own_cancel')
    keyboard.add(btn_cancel)
    return keyboard


def cancel_br_start():
    keyboard = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data='br_start_cancel')
    keyboard.add(btn_cancel)
    return keyboard


def return_admin_rights():
    keyboard = types.InlineKeyboardMarkup()
    btn_return_adm = types.InlineKeyboardButton("🔓 Восстановить права", callback_data='return_adm')
    keyboard.add(btn_return_adm)
    return keyboard


def accept_send(type_broadcast='msg'):
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Отправить рассылку", callback_data=f'br_accept_{type_broadcast}')
    btn_cancel = types.InlineKeyboardButton("❌ Отменить отправку", callback_data=f'br_cancel')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


def settings_keyboard():
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


def water_setup_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    water_target = types.InlineKeyboardButton("🎯 Цель на день", callback_data='water_goal')
    water_reminder = types.InlineKeyboardButton("⏰ Напоминания", callback_data='water_reminder')
    water_exit = types.InlineKeyboardButton("🚶 Назад", callback_data='water_stg_cancel')
    keyboard.add(water_target, water_reminder, water_exit)
    return keyboard


def water_goal_keyboard():
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


def water_goal_custom_cancel():
    keyboard = types.InlineKeyboardMarkup()
    water_exit = types.InlineKeyboardButton("❌ Отмена", callback_data='water_goal_custom_cancel')
    keyboard.add(water_exit)
    return keyboard


def get_water_reminder_type_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    type_interval = types.InlineKeyboardButton("⏰ По интервалу", callback_data='type_interval')
    type_smart = types.InlineKeyboardButton("🤖 Умный режим", callback_data='type_smart')
    water_reminder_type_cancel = types.InlineKeyboardButton("🔙 Назад", callback_data='water_reminder_exit')
    keyboard.add(type_interval, type_smart, water_reminder_type_cancel)
    return keyboard


def get_water_interval_keyboard():
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


def water_add_keyboard():
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


def support_selection_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    technical_support = types.InlineKeyboardButton("🔧 Техподдержка", callback_data='technical_support')
    personal_consultation = types.InlineKeyboardButton("👨‍⚕️ Консультация", callback_data='personal_consultation')
    my_tickets = types.InlineKeyboardButton("📋 Мои обращения", callback_data='my_tickets')
    supp_exit = types.InlineKeyboardButton("🔙  Выйти", callback_data='supp_exit')
    keyboard.add(technical_support, personal_consultation,
                 my_tickets, supp_exit)
    return keyboard


def technical_support_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    tech_supp_open_ticket = types.InlineKeyboardButton("📨 Открыть обращение", callback_data='tech_supp_open_ticket')
    supp_cancel_opening = types.InlineKeyboardButton("🚫 Отмена", callback_data='supp_cancel_opening')
    keyboard.add(tech_supp_open_ticket, supp_cancel_opening)
    return keyboard


def consultation_support_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    tech_supp_open_ticket = types.InlineKeyboardButton("📨 Открыть обращение", callback_data='consult_supp_open_ticket')
    supp_cancel_opening = types.InlineKeyboardButton("🚫 Отмена", callback_data='supp_cancel_opening')
    keyboard.add(tech_supp_open_ticket, supp_cancel_opening)
    return keyboard


def supp_ticket_cancel_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    supp_ticket_exit = types.InlineKeyboardButton("❌ Отмена", callback_data='supp_ticket_exit')
    keyboard.add(supp_ticket_exit)
    return keyboard


def supp_ticket_draft_keyboard(id_ticket):
    keyboard = types.InlineKeyboardMarkup()
    go_to_chat = types.InlineKeyboardButton("💬 К диалогу",
                                            callback_data=f'accept_ticket_{id_ticket}')
    delete = types.InlineKeyboardButton("🚫 Удалить",
                                        callback_data=f'delete_ticket_{id_ticket}')
    keyboard.add(go_to_chat, delete)
    return keyboard


def go_to_ticket_keyboard(ticket_id, role):
    keyboard = types.InlineKeyboardMarkup()
    open_ticket = types.InlineKeyboardButton("📨 Открыть обращение", callback_data=f'open_ticket_{ticket_id}_{role}')
    keyboard.add(open_ticket)
    return keyboard


def opening_ticket_keyboard(role, ticket_info, page=1):
    type = ticket_info[0]
    ticket_list = ticket_info[1]
    ticket_list.sort(key=sort_ticket)
    count_ticket = len(ticket_list)
    total_page = -(-count_ticket // 10)  # Округление вверх
    first_ticket_in_page = page * 10 - 10
    last_ticket_in_page = page * 10 + 1
    keyboard = types.InlineKeyboardMarkup()
    for i in ticket_list[first_ticket_in_page:last_ticket_in_page]:
        emoji = '🆕' if i[2] == 'new' else None
        keyboard.row(
            types.InlineKeyboardButton(
                f"{emoji if emoji else ''} {i[0]}",
                callback_data=f'open_ticket_{i[1]}_{role}'))
    page_management_buttons = []
    if page > 1:
        page_management_buttons.append(
            types.InlineKeyboardButton(
                '⬅️ Назад', callback_data=f'tickets_page_{page - 1}_{role}{'_' + type if role == 'admin' else ''}')
        )
    else:
        page_management_buttons.append(types.InlineKeyboardButton("🔙  Выйти", callback_data=f'tickets_exit_{role}'))
    page_management_buttons.append(types.InlineKeyboardButton(
        f'📄 {page}/{total_page}', callback_data='info_page')
    )
    if total_page > page:
        page_management_buttons.append(types.InlineKeyboardButton(
            "▶️ Вперед", callback_data=f"tickets_page_{page + 1}_{role}{'_' + type if role == 'admin' else ''}")
        )
    keyboard.row(*page_management_buttons)
    return keyboard


def ticket_actions_keyboard(messages_id=None, role='user', type=None, id_ticket=None, photos_id=None):
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

def cancel_photo_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    cancel_btn = types.InlineKeyboardButton('⬅️ Закрыть', callback_data='cancel_photo')
    keyboard.add(cancel_btn)
    return keyboard
def admin_ticket_section_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton("🔧 Техподдержка", callback_data="adm_tickets_tech"),
        types.InlineKeyboardButton("👨‍⚕️ Консультации", callback_data="adm_tickets_consult"),
        types.InlineKeyboardButton("🔙 Назад", callback_data="adm_back_main")
    )

    return keyboard


def accept_aggressive_title_keyboard(title, type_ticket):
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить",
                                            callback_data=f'aggressive_title_accept_{title}_{type_ticket}')
    btn_cancel = types.InlineKeyboardButton("❌ Отменить", callback_data=f'aggressive_title_cancel')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


def accept_aggressive_msg_keyboard(ticket_id, text):
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить отправку",
                                            callback_data=f'aggressive_msg_to_ticket_accept_{ticket_id}_{text}')
    btn_cancel = types.InlineKeyboardButton("❌ Отменить отправку",
                                            callback_data=f'aggressive_msg_to_ticket_cancel_{ticket_id}')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


def accept_custom_add_water_keyboard(amount_ml):
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'water_add_{amount_ml}')
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=f'water_add_custom_cancel')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard


def cancel_custom_add_water_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=f'water_add_custom_cancel')
    keyboard.add(btn_cancel)
    return keyboard


def accept_delete_ticket_keyboard(ticket_id):
    keyboard = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f'delete_ticket_{ticket_id}')
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=f'cancel_delete_ticket_{ticket_id}')
    keyboard.add(btn_accept, btn_cancel)
    return keyboard
