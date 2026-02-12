import telebot
import re
import logging
import time
from requests.exceptions import ReadTimeout, ConnectionError
from database import init_db, add_user, update_user_activity_smart, get_all_admin, update_username, replace_status, \
    get_user_status, water_set_reminder_type, update_goal, count_users_trackers, water_stats, get_timezone, \
    set_timezone, add_water_ml, update_last_add_water_ml, tickets_by_user, \
    validate_water_addition, delete_ticket, load_tickets_info, count_tickets_for_admin, send_supp_msg, add_ticket
from handlers.admin_notifications import return_admin_notify, new_ticket_notify
from handlers.broadcast import broadcast_send, accept_broadcast
from handlers.owner_menu import add_admin, remove_admin
from handlers.reminders import UniversalReminderService
from handlers.support import create_ticket, opening_ticket
from handlers.water import add_custom_water
from keyboards import main_menu, admin_menu, owner_menu, cancel_br_start, own_cancel, settings_keyboard, \
    water_setup_keyboard, water_goal_keyboard, water_goal_custom_cancel, get_water_reminder_type_keyboard, \
    get_water_interval_keyboard, water_add_keyboard, timezone_selection_keyboard, support_selection_keyboard, \
    consultation_support_keyboard, technical_support_keyboard, supp_ticket_cancel_keyboard, opening_ticket_keyboard, \
    admin_ticket_section_keyboard, cancel_custom_add_water_keyboard, supp_ticket_draft_keyboard, \
    accept_delete_ticket_keyboard
from messages import start_message, nf_cmd, adm_start_message, exit_home, example_broadcast, cancellation, \
    add_new_adm_msg, remove_adm_msg, user_return_admin_msg, succ_return_adm, owner_unban, already_return_adm_msg, \
    error_msg, settings_msg, water_tracker_setup_msg, water_goal_selection_msg, water_goal_success_msg, \
    water_goal_custom_msg, water_reminder_type_selection_msg, water_reminder_type_smart_msg, water_interval_setup_msg, \
    water_interval_selected_short_msg, water_setup_required_msg, water_tracker_dashboard_msg, water_goal_not_set_msg, \
    timezone_selection_msg, timezone_suc_msg, add_water_msg, support_selection_msg, support_tech_msg, \
    support_consult_msg, create_ticket_msg, no_active_tickets_msg, send_msg_to_ticket_msg, opening_ticket_msg, \
    open_ticket_msg, ticket_closed_msg, my_tickets_msg, admin_ticket_section_msg, admin_tickets_msg, \
    water_add_custom_input_msg, succ_ticket_title_msg, confirm_delete_ticket_msg
from handlers.settings import water_goal_custom_stg
from handlers.sleeps import sleeps_main
from handlers.sports import sports_main
from handlers.stats import adm_stats, owner_stats
from config import token, is_admin, is_owner, owners_copy

bot = telebot.TeleBot(token)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Ошибка в {func.__name__}: {e}")
            chat_id = None
            if len(args) > 0:
                if hasattr(args[0], 'chat'):
                    chat_id = args[0].chat.id
                elif hasattr(args[0], 'message') and hasattr(args[0].message, 'chat'):
                    chat_id = args[0].message.chat.id

            if chat_id:
                try:
                    bot.send_message(chat_id, error_msg)
                except:
                    pass

    return wrapper


@bot.message_handler(commands=['start'])
# @error_handler
def start(message):
    logging.info(f"Пользователь {message.chat.id} запустил бота")
    if is_owner(message.chat.id):
        add_user(message.chat.id, message.from_user.username,
                 'Owner')

    else:
        add_user(message.chat.id, message.from_user.username,
                 f"{'Admin' if is_admin(message.chat.id) else 'User'}")
    if get_timezone(message.chat.id) is not None:
        bot.send_message(
            message.chat.id,
            start_message(message.from_user.first_name),
            reply_markup=main_menu(message.chat.id)
        )
    else:
        bot.send_message(message.chat.id,
                         timezone_selection_msg(
                             message.from_user.first_name),
                         reply_markup=timezone_selection_keyboard()
                         )


@bot.message_handler(content_types=['text'])
# @error_handler
def msg(message):
    update_username(message.chat.id, message.from_user.username, bot)
    update_user_activity_smart(message.chat.id)
    match message.text:
        case "💧 Водный баланс":
            if count_users_trackers('track_water', 'goal_ml', message.chat.id):
                current_goal, water_drunk = water_stats(message.chat.id)
                bot.send_message(message.chat.id,
                                 water_tracker_dashboard_msg(
                                     message.from_user.first_name,
                                     current_goal, water_drunk),
                                 reply_markup=water_add_keyboard()
                                 )
            else:
                bot.send_message(message.chat.id,
                                 water_goal_not_set_msg)
        case "💪 Физ-активность":
            bot.send_message(message.chat.id, sports_main())

        case "😴 Сон":
            bot.send_message(message.chat.id, sleeps_main())

        case "📊 Статистика":
            bot.send_message(message.chat.id, "тут будет статистика")

        case "⚙️ Настройки":
            bot.send_message(
                message.chat.id,
                settings_msg(message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case "👨‍⚕️ Персональный специалист":
            bot.send_message(message.chat.id, support_selection_msg(
                message.from_user.first_name),
                             reply_markup=support_selection_keyboard()
                             )

        case '🛠️ Админ панель' if is_admin(message.chat.id):
            bot.send_message(
                message.chat.id,
                adm_start_message(message.from_user.first_name,
                                  message.chat.id),
                reply_markup=admin_menu(message.chat.id)
            )

        case "📊 Статистика пользователей" if is_admin(message.chat.id):
            bot.send_message(message.chat.id, adm_stats())
        case '📢 Рассылка' if is_admin(message.chat.id):
            bot.send_message(message.chat.id,
                             example_broadcast, reply_markup=cancel_br_start())
            bot.register_next_step_handler_by_chat_id(
                message.chat.id,
                lambda msg: accept_broadcast(msg, bot)
            )
        case '👨‍⚕️ Обращения' if is_admin(message.chat.id):
            bot.send_message(message.chat.id,
                             admin_ticket_section_msg(
                                 message.from_user.first_name),
                             reply_markup=admin_ticket_section_keyboard()
                             )
        case "👑 Управление администрацией" if is_owner(message.chat.id):
            bot.send_message(message.chat.id, owner_stats(get_all_admin()), reply_markup=owner_menu())
        case "↩️ На главную":
            bot.send_message(
                message.chat.id, exit_home(),
                reply_markup=main_menu(message.chat.id)
            )
        case _:
            bot.send_message(message.chat.id, nf_cmd)


@bot.callback_query_handler(func=lambda call: True)
# @error_handler
def callback_inline(call):
    match call.data:
        case 'timezone_-1' | 'timezone_0' | 'timezone_1' | 'timezone_2' | \
             'timezone_3' | 'timezone_4' | 'timezone_5' | \
             'timezone_6' | 'timezone_7' | 'timezone_8' | 'timezone_9':
            timezone_offset = int(call.data.split('_')[1])
            old_timezone = get_timezone(call.message.chat.id)
            set_timezone(call.message.chat.id, timezone_offset)
            bot.answer_callback_query(call.id, timezone_suc_msg, show_alert=False)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if old_timezone is None:
                bot.send_message(
                    call.message.chat.id,
                    start_message(call.from_user.first_name),
                    reply_markup=main_menu(call.message.chat.id)
                )
        case 'br_accept':
            broadcast_send(call, bot)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'br_cancel':
            bot.send_message(call.message.chat.id, cancellation)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'add_adm':
            bot.send_message(call.message.chat.id, add_new_adm_msg, reply_markup=own_cancel())
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: add_admin(msg, bot)
            )

            bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'remove_adm':
            bot.send_message(call.message.chat.id, remove_adm_msg, reply_markup=own_cancel())
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: remove_admin(msg, bot)
            )
            bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'own_cancel':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
            bot.answer_callback_query(call.id, cancellation, show_alert=False)
            bot.send_message(call.message.chat.id, owner_stats(get_all_admin()), reply_markup=owner_menu())
        case 'br_start_cancel':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
            bot.send_message(call.message.chat.id, cancellation)
        case 'return_adm':
            user_id = int(re.search(r'ID Нарушителя: (\d+)', call.message.text).group(1))
            if user_id in owners_copy:
                bot.send_message(call.message.chat.id, owner_unban)
            elif get_user_status(user_id=user_id) == "Admin":
                bot.send_message(call.mesage.chat.id, already_return_adm_msg)
            else:
                replace_status('Admin', user_id=user_id)
                bot.send_message(user_id, user_return_admin_msg)
                bot.send_message(call.message.chat.id, succ_return_adm)
                return_admin_notify(bot, user_id, call.message.chat.id)
            bot.delete_message(call.message.chat.id, call.message.message_id)

        case 'water_settings':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )
        case 'activity_settings':
            pass
        case 'dream_settings':
            pass

        case 'review_settings':
            pass
        case 'timezone_settings':
            bot.send_message(call.message.chat.id,
                             timezone_selection_msg(
                                 call.message.from_user.first_name),
                             reply_markup=timezone_selection_keyboard()
                             )

        case 'water_reminder':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if count_users_trackers('track_water', 'goal_ml', call.message.chat.id):
                bot.send_message(
                    call.message.chat.id,
                    water_reminder_type_selection_msg(
                        call.from_user.first_name)
                    , reply_markup=get_water_reminder_type_keyboard()
                )
            else:
                bot.send_message(call.message.chat.id,
                                 water_setup_required_msg,
                                 reply_markup=water_goal_keyboard())
        case 'type_smart':
            bot.answer_callback_query(call.id, water_reminder_type_smart_msg, show_alert=False)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            water_set_reminder_type(call.message.chat.id, 'Smart')
            bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )
        case 'type_interval':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id, water_interval_setup_msg(call.from_user.first_name),
                reply_markup=get_water_interval_keyboard()
            )
        case 'water_interval_1h' | 'water_interval_2h' | 'water_interval_3h' | 'water_interval_4h' | 'water_interval_5h':
            interval = int(call.data[-2])
            bot.answer_callback_query(call.id, water_interval_selected_short_msg(interval), show_alert=False)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )
            water_set_reminder_type(call.message.chat.id, 'Interval', interval)
        case 'water_interval_exit':
            bot.answer_callback_query(call.id, cancellation, show_alert=False)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                water_reminder_type_selection_msg(
                    call.from_user.first_name)
                , reply_markup=get_water_reminder_type_keyboard()
            )
        case 'water_goal':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id,
                             water_goal_selection_msg(call.from_user.first_name),
                             reply_markup=water_goal_keyboard()
                             )
        case 'water_goal_1500' | 'water_goal_2000' | 'water_goal_2500' | 'water_goal_3000':
            goal_ml = int((call.data[11:]))
            update_goal(call.from_user.id, goal_ml)
            bot.answer_callback_query(call.id, water_goal_success_msg(goal_ml))
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name),
                reply_markup=water_setup_keyboard()
            )

        case 'water_goal_custom':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_custom_selection_msg = bot.send_message(
                call.message.chat.id,
                water_goal_custom_msg, reply_markup=water_goal_custom_cancel()
            )
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: water_goal_custom_stg(bot, msg, call, send_custom_selection_msg)
            )
        case 'water_goal_exit' | 'water_reminder_exit':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, cancellation, show_alert=False)
            bot.send_message(
                call.message.chat.id,
                water_tracker_setup_msg(call.from_user.first_name)
                , reply_markup=water_setup_keyboard()
            )
        case 'water_goal_custom_cancel':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, cancellation, show_alert=False)
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
            bot.send_message(call.message.chat.id,
                             water_goal_selection_msg(call.from_user.first_name),
                             reply_markup=water_goal_keyboard()
                             )
        case 'water_stg_cancel':
            bot.answer_callback_query(call.id, cancellation, show_alert=False)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                settings_msg(call.message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case 'cancel_settings' | 'water_add_exit':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                exit_home(),
                reply_markup=main_menu(call.message.chat.id)
            )
        case data if (data.startswith('water_add')
                      and len(data.split('_')) == 3
                      and data.split('_')[-1].isdigit()):
            water_add = call.data.split('_')[2]
            accept, msg = validate_water_addition(call.message.chat.id, water_add)

            if accept:
                update_last_add_water_ml(call.message.chat.id)
                add_water_ml(call.message.chat.id, water_add)
                bot.answer_callback_query(call.id, add_water_msg)
                bot.delete_message(call.message.chat.id, call.message.message_id)
                current_goal, water_drunk = water_stats(call.message.chat.id)
                bot.send_message(call.message.chat.id,
                                 water_tracker_dashboard_msg(
                                     call.from_user.first_name,
                                     current_goal, water_drunk),
                                 reply_markup=water_add_keyboard()
                                 )
            if msg:
                bot.send_message(call.message.chat.id, msg)
        case 'water_add_custom':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id,
                             water_add_custom_input_msg(
                                 call.message.from_user.first_name),
                                 reply_markup=cancel_custom_add_water_keyboard()
                             )
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: add_custom_water(msg, bot)
            )
        case 'custom_water_add_cancel':
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
            bot.answer_callback_query(call.id, cancellation, show_alert=False)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            current_goal, water_drunk = water_stats(call.message.chat.id)
            bot.send_message(call.message.chat.id,
                             water_tracker_dashboard_msg(
                                 call.message.from_user.first_name,
                                 current_goal, water_drunk),
                             reply_markup=water_add_keyboard()
                             )
        case 'technical_support' | 'personal_consultation':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id,
                             support_tech_msg if call.data == 'technical_support'
                             else support_consult_msg,
                             reply_markup=technical_support_keyboard()
                             if call.data == 'technical_support'
                             else consultation_support_keyboard()
                             )
        case 'tech_supp_open_ticket' | 'consult_supp_open_ticket':
            type_supp = call.data.split('_')[0]
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, create_ticket_msg(type_supp),
                             reply_markup=supp_ticket_cancel_keyboard())
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: create_ticket(msg, bot, type_supp)
            )
        case 'supp_exit':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, exit_home(),
                             reply_markup=main_menu(call.message.chat.id))
        case data if data.startswith('accept_ticket_'):
            id_ticket = data.split('_')[2]
            bot.answer_callback_query(call.id, opening_ticket_msg)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            opening_ticket(call.message, bot, id_ticket, 'user')
        case data if data.startswith('confirm_delete_ticket_'):
            ticket_id = data.split('_')[3]
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                confirm_delete_ticket_msg(ticket_id),
                reply_markup=accept_delete_ticket_keyboard(ticket_id)
            )
        case data if data.startswith('cancel_delete_ticket_'):
            id_ticket = data.split('_')[3]
            bot.answer_callback_query(call.id, cancellation)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            opening_ticket(call.message, bot, id_ticket, 'user')
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
        case data if data.startswith('delete_ticket_'):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            id_ticket = data.split('_')[2]
            delete_ticket(id_ticket)
            bot.send_message(call.message.chat.id, ticket_closed_msg(id_ticket))

        case data if data.startswith('aggressive_title_'):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if data.split('_')[2] == 'accept':
                title,type_ticket = data.split('_')[3],data.split('_')[4]
                id_ticket = add_ticket(title, call.message.chat.id,
                                       call.message.from_user.username,
                                       call.message.from_user.first_name,
                                       type_ticket
                                       )
                bot.send_message(call.message.chat.id, succ_ticket_title_msg,
                                 reply_markup=supp_ticket_draft_keyboard(id_ticket))
                new_ticket_notify(bot, id_ticket, call.message.chat.id, type_ticket)
            else:
                bot.send_message(call.message.chat.id, ticket_closed_msg())
        case 'my_tickets':
            if tickets_by_user(call.message.chat.id):
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(
                    call.message.chat.id,
                    my_tickets_msg,
                    reply_markup=opening_ticket_keyboard('user',
                                                         load_tickets_info(call.message.chat.id))
                )
            else:
                bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
        case data if data.startswith('msg_to_ticket_'):
            ticket_id = data.split('_')[4]
            if data.split('_')[3] == 'accept':
                bot.delete_message(call.message.chat.id, call.message.message_id)
                text = data.split('_')[5]
                send_supp_msg(ticket_id, text, 1)
                opening_ticket(call.message, bot, ticket_id, 'user')
            else:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id, cancellation, show_alert=False)
                opening_ticket(call.message, bot, ticket_id, 'user')
        case data if data.startswith('ticket_exit'):
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            role = 'admin' if call.data.split('_')[-2] == 'admin' else 'user'
            try:
                limit = -2 if role == 'admin' else -1
                for i in data.split('_')[2:limit]:
                    bot.delete_message(call.message.chat.id, int(i))
            except:
                pass
            if role == 'user':
                if tickets_by_user(call.message.chat.id):
                    bot.send_message(
                        call.message.chat.id,
                        my_tickets_msg,
                        reply_markup=opening_ticket_keyboard('user',
                                                             load_tickets_info(call.message.chat.id))
                    )
                else:
                    bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
            else:
                type_supp = call.data.split('_')[-1]
                if count_tickets_for_admin(type_supp):
                    bot.send_message(call.message.chat.id
                                     , admin_tickets_msg(type_supp),
                                     reply_markup=
                                     opening_ticket_keyboard('admin', load_tickets_info(role='admin', type=type_supp)
                                                             ))
                else:
                    bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
        case 'adm_tickets_tech' | 'adm_tickets_consult':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            type_supp = call.data.split('_')[2]
            if count_tickets_for_admin(type_supp):
                bot.send_message(call.message.chat.id
                                 , admin_tickets_msg(type_supp),
                                 reply_markup=
                                 opening_ticket_keyboard('admin', load_tickets_info(role='admin', type=type_supp)
                                                         ))
            else:
                bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)
        case data if data.startswith('tickets_exit'):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            if data.split('_')[2] == 'user':
                bot.send_message(call.message.chat.id, support_selection_msg(
                    call.message.from_user.first_name),
                                 reply_markup=support_selection_keyboard()
                                 )
            else:
                bot.send_message(call.message.chat.id,
                                 admin_ticket_section_msg(
                                     call.message.from_user.first_name),
                                 reply_markup=admin_ticket_section_keyboard()
                                 )
        case 'adm_back_main':
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id,
                             exit_home('Админ'),
                             reply_markup=admin_menu(call.message.chat.id)
                             )
        case data if data.startswith('tickets_page_'):
            print(data)
            page, role = data.split('_')[2], data.split('_')[3]
            if role == 'admin':
                type = data.split('_')[4]
                text = admin_tickets_msg(type)
            else:
                type = None
                text = my_tickets_msg
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, text,
                             reply_markup=opening_ticket_keyboard(
                                 role, load_tickets_info(call.message.chat.id, role=role, type=type),
                                 int(page))
                             )
        case data if data.startswith('open_ticket_'):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            ticket_id, role = data.split('_')[2], data.split('_')[3]
            opening_ticket(call.message, bot, ticket_id, role)

        case 'supp_cancel_opening' | 'supp_ticket_exit':
            bot.answer_callback_query(call.id, cancellation, show_alert=False)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, support_selection_msg(
                call.message.from_user.first_name),
                             reply_markup=support_selection_keyboard()
                             )


def start_bot():
    init_db()
    reminder_service =  UniversalReminderService(bot)
    reminder_service.start()
    while True:
        try:
            logging.info("Бот запущен")
            bot.polling(
                none_stop=True,
                timeout=30,
                long_polling_timeout=10,
            )
        except (ReadTimeout, ConnectionError, telebot.apihelper.ApiException) as e:

            logging.error(f"Произошла ошибка: {e}. Перезапуск через 15 секунд...")
            time.sleep(15)
        except KeyboardInterrupt:
            logging.info('Бот принудительно остановлен')
            reminder_service.stop()
            break

    # except Exception as e:
    # logging.error(f"Непредвиденная ошибка: {e}. Перезапуск через 30 секунд...")

    # time.sleep(30)


if __name__ == '__main__':
    start_bot()
