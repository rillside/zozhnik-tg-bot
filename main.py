import asyncio
import telebot
from telebot.async_telebot import AsyncTeleBot
from functools import wraps
import logging
import time
from requests.exceptions import ReadTimeout, ConnectionError
from database import init_db, add_user, update_user_activity_smart, get_all_admin, update_username, \
    count_users_trackers, water_stats, get_timezone, tickets_by_user, load_tickets_info
from handlers.broadcast import broadcast_send, accept_broadcast
from handlers.owner_menu import add_admin, remove_admin, return_admin
from handlers.reminders import UniversalReminderService
from handlers.support import create_ticket, opening_ticket, handle_delete_ticket, \
    handling_aggressive_content, ticket_exit, admin_look_tickets, tickets_exit, look_ticket_page
from handlers.water import handle_add_water
from keyboards import main_menu, admin_menu, owner_menu, cancel_br_start, own_cancel, settings_keyboard, \
    water_setup_keyboard, water_goal_keyboard, get_water_interval_keyboard, water_add_keyboard, \
    timezone_selection_keyboard, support_selection_keyboard, consultation_support_keyboard, \
    technical_support_keyboard, supp_ticket_cancel_keyboard, opening_ticket_keyboard, \
    admin_ticket_section_keyboard
from messages import start_message, nf_cmd, adm_start_message, exit_home, example_broadcast, cancellation, \
    add_new_adm_msg, remove_adm_msg, \
    error_msg, settings_msg, water_tracker_setup_msg, water_goal_selection_msg, water_interval_setup_msg, \
    water_tracker_dashboard_msg, water_goal_not_set_msg,timezone_selection_msg, support_selection_msg, \
    support_tech_msg, support_consult_msg, create_ticket_msg, no_active_tickets_msg, opening_ticket_msg, \
    my_tickets_msg,admin_ticket_section_msg
from handlers.settings import set_reminder_type_water, water_smart_type_install, \
    water_setting_interval, select_timezone, water_goal_settings
from handlers.sleeps import sleeps_main
from handlers.sports import sports_main
from handlers.stats import adm_stats, owner_stats
from config import token, is_admin, is_owner

bot = AsyncTeleBot(token)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)


def error_handler(func):
    @wraps
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
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
                    await bot.send_message(chat_id, error_msg)
                except:
                    pass

    return wrapper


@bot.message_handler(commands=['start'])
# @error_handler
async def start(message):
    logging.info(f"Пользователь {message.chat.id} запустил бота")
    if is_owner(message.chat.id):
        await add_user(message.chat.id, message.from_user.username,
                 'Owner')

    else:
        await add_user(message.chat.id, message.from_user.username,
                 f"{'Admin' if is_admin(message.chat.id) else 'User'}")
    if await get_timezone(message.chat.id) is not None:
        await bot.send_message(
            message.chat.id,
            start_message(message.from_user.first_name),
            reply_markup=main_menu(message.chat.id)
        )
    else:
        await bot.send_message(message.chat.id,
                         timezone_selection_msg(
                             message.from_user.first_name),
                         reply_markup=timezone_selection_keyboard()
                         )


@bot.message_handler(content_types=['text'])
# @error_handler
async def msg(message):
    await update_username(message.chat.id, message.from_user.username, bot)
    await update_user_activity_smart(message.chat.id)
    match message.text:
        case "💧 Водный баланс":
            if await count_users_trackers('track_water', 'goal_ml', message.chat.id):
                current_goal, water_drunk = await water_stats(message.chat.id)
                await bot.send_message(message.chat.id,
                                 water_tracker_dashboard_msg(
                                     message.from_user.first_name,
                                     current_goal, water_drunk),
                                 reply_markup=water_add_keyboard()
                                 )
            else:
                await bot.send_message(message.chat.id,
                                 water_goal_not_set_msg)
        case "💪 Физ-активность":
            await bot.send_message(message.chat.id, sports_main())

        case "😴 Сон":
            await bot.send_message(message.chat.id, sleeps_main())

        case "📊 Статистика":
            await bot.send_message(message.chat.id, "тут будет статистика")

        case "⚙️ Настройки":
            await bot.send_message(
                message.chat.id,
                settings_msg(message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case "👨‍⚕️ Персональный специалист":
            await bot.send_message(message.chat.id, support_selection_msg(
                message.from_user.first_name),
                             reply_markup=support_selection_keyboard()
                             )

        case '🛠️ Админ панель' if is_admin(message.chat.id):
            await bot.send_message(
                message.chat.id,
                adm_start_message(message.from_user.first_name,
                                  message.chat.id),
                reply_markup=admin_menu(message.chat.id)
            )

        case "📊 Статистика пользователей" if is_admin(message.chat.id):
            await bot.send_message(message.chat.id, adm_stats())
        case '📢 Рассылка' if is_admin(message.chat.id):
            await bot.send_message(message.chat.id,
                             example_broadcast, reply_markup=cancel_br_start())
            bot.register_next_step_handler_by_chat_id(
                message.chat.id,
                lambda msg: accept_broadcast(msg, bot)
            )
        case '👨‍⚕️ Обращения' if is_admin(message.chat.id):
            await bot.send_message(message.chat.id,
                             admin_ticket_section_msg(
                                 message.from_user.first_name),
                             reply_markup=admin_ticket_section_keyboard()
                             )
        case "👑 Управление администрацией" if is_owner(message.chat.id):
            await bot.send_message(message.chat.id, await owner_stats(), reply_markup=owner_menu())
        case "↩️ На главную":
            await bot.send_message(
                message.chat.id, exit_home(),
                reply_markup=main_menu(message.chat.id)
            )
        case _:
            await bot.send_message(message.chat.id, nf_cmd)


@bot.callback_query_handler(func=lambda call: True)
# @error_handler
async def callback_inline(call):
    match call.data:
        case data if data.startswith('timezone_'):
            await select_timezone(call, bot)
        case 'br_accept':
            await broadcast_send(call, bot)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'br_cancel':
            await bot.send_message(call.message.chat.id, cancellation)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'add_adm':
            await bot.send_message(call.message.chat.id, add_new_adm_msg, reply_markup=own_cancel())
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: add_admin(msg, bot)
            )

            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'remove_adm':
            await bot.send_message(call.message.chat.id, remove_adm_msg, reply_markup=own_cancel())
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: remove_admin(msg, bot)
            )
            await bot.delete_message(call.message.chat.id, call.message.message_id)
        case 'own_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.send_message(call.message.chat.id, await owner_stats(), reply_markup=owner_menu())
        case 'br_start_cancel':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.clear_step_handler_by_chat_id(call.message.chat.id)
            await bot.send_message(call.message.chat.id, cancellation)
        case 'return_adm':
            await return_admin(call, bot)

        case 'water_settings':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
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
            await bot.send_message(call.message.chat.id,
                             timezone_selection_msg(
                                 call.message.from_user.first_name),
                             reply_markup=timezone_selection_keyboard()
                             )

        case 'water_reminder':
            await set_reminder_type_water(call, bot)
        case 'type_smart':
            await water_smart_type_install(call, bot)
        case 'type_interval':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id, water_interval_setup_msg(call.from_user.first_name),
                reply_markup=get_water_interval_keyboard()
            )
        case data if data.startswith('water_interval_'):
            step = 'exit' if data.split('_')[-1] == 'exit' else 'install'
            await water_setting_interval(call, bot, step)
        case 'water_goal':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                             water_goal_selection_msg(call.from_user.first_name),
                             reply_markup=water_goal_keyboard()
                             )
        case data if data.startswith('water_goal_') or data == 'water_reminder_exit':
            match call.data.split('_')[-1]:
                case 1500 | 2000 | 2500 | 3000:
                    step = 'set_goal'
                case 'custom':
                    step = 'set_goal_custom'
                case 'exit':
                    step = 'exit'
                case 'cancel':
                    step = 'cancel_custom'
            await water_goal_settings(call, bot, step)

        case 'water_stg_cancel':
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                settings_msg(call.message.from_user.first_name),
                reply_markup=settings_keyboard()
            )
        case 'cancel_settings' | 'water_add_exit':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(
                call.message.chat.id,
                exit_home(),
                reply_markup=main_menu(call.message.chat.id)
            )
        case data if ((data == 'water_add_custom'
                       or data == 'water_add_custom_cancel')
                      or (data.startswith('water_add')
                          and len(data.split('_')) == 3
                          and data.split('_')[-1].isdigit())):
            match data.split('_')[-1]:
                case 'custom':
                    step = 'request_value'
                case 'cancel':
                    step = 'custom_cancel'
                case _:
                    step = 'addition'
            await handle_add_water(call, bot, step)
        case 'technical_support' | 'personal_consultation':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                             support_tech_msg if call.data == 'technical_support'
                             else support_consult_msg,
                             reply_markup=technical_support_keyboard()
                             if call.data == 'technical_support'
                             else consultation_support_keyboard()
                             )
        case 'tech_supp_open_ticket' | 'consult_supp_open_ticket':
            type_supp = call.data.split('_')[0]
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, create_ticket_msg(type_supp),
                             reply_markup=supp_ticket_cancel_keyboard())
            bot.register_next_step_handler_by_chat_id(
                call.message.chat.id,
                lambda msg: create_ticket(msg, bot, type_supp)
            )
        case 'supp_exit':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, exit_home(),
                             reply_markup=main_menu(call.message.chat.id))
        case data if data.startswith('accept_ticket_'):
            id_ticket = data.split('_')[2]
            await bot.answer_callback_query(call.id, opening_ticket_msg)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await opening_ticket(call.message, bot, id_ticket, 'user')
        case data if data.startswith(('delete_ticket_',
                                      'confirm_delete_ticket_',
                                      'cancel_delete_ticket_')
                                     ):
            type_handle = data.split('_')[0]
            await handle_delete_ticket(call, bot, type_handle)

        case data if data.startswith(('aggressive_title_', 'aggressive_msg_to_ticket_')):
            content_type = 'msg' if data.split('_')[1] == 'msg' else 'title'
            await handling_aggressive_content(call, bot, content_type)
        case 'my_tickets':
            if tickets_by_user(call.message.chat.id):
                await bot.delete_message(call.message.chat.id, call.message.message_id)
                await bot.send_message(
                    call.message.chat.id,
                    my_tickets_msg,
                    reply_markup=opening_ticket_keyboard('user',
                                                         await load_tickets_info(call.message.chat.id))
                )
            else:
                await bot.answer_callback_query(call.id, no_active_tickets_msg, show_alert=False)

        case data if data.startswith('ticket_exit'):
            await ticket_exit(call, bot)
        case 'adm_tickets_tech' | 'adm_tickets_consult':
            await admin_look_tickets(call,bot)
        case data if data.startswith('tickets_exit'):
            await tickets_exit(call,bot)
        case 'adm_back_main':
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id,
                             exit_home('Админ'),
                             reply_markup=admin_menu(call.message.chat.id)
                             )
        case data if data.startswith('tickets_page_'):
            await look_ticket_page(call,bot)
        case data if data.startswith('open_ticket_'):
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            ticket_id, role = data.split('_')[2], data.split('_')[3]
            await opening_ticket(call.message, bot, ticket_id, role)

        case 'supp_cancel_opening' | 'supp_ticket_exit':
            await bot.answer_callback_query(call.id, cancellation, show_alert=False)
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await bot.send_message(call.message.chat.id, support_selection_msg(
                call.message.from_user.first_name),
                             reply_markup=support_selection_keyboard()
                             )


async def start_bot():
    await init_db()
    reminder_service = UniversalReminderService(bot)
    await reminder_service.start()
    while True:
        try:
            logging.info("Бот запущен")
            await bot.polling(none_stop=True)
        except (ReadTimeout, ConnectionError, telebot.apihelper.ApiException) as e:

            logging.error(f"Произошла ошибка: {e}. Перезапуск через 15 секунд...")
            await asyncio.sleep(15)
        except KeyboardInterrupt:
            logging.info('Бот принудительно остановлен')
            await reminder_service.stop()
            break

    # except Exception as e:
    # logging.error(f"Непредвиденная ошибка: {e}. Перезапуск через 30 секунд...")

    # await asyncio.sleep(30)


if __name__ == '__main__':
    asyncio.run(start_bot())
