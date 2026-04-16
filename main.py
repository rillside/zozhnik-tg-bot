import asyncio
import logging
import signal
from functools import wraps
from typing import Any, Callable

import telebot
from requests.exceptions import ConnectionError, ReadTimeout
from telebot.async_telebot import AsyncTeleBot

from config import is_admin, is_owner, token
from database import (
    add_user,
    get_timezone,
    init_db,
    is_user_banned,
    update_user_activity_smart,
    update_username,
)
from handlers.routers.callback_router import route_callback
from handlers.routers.fsm_router import handle_fsm_photo, handle_fsm_text, handle_fsm_video
from handlers.routers.message_router import handle_main_message
from keyboards import main_menu, timezone_selection_keyboard
from messages import banned_msg, error_msg, start_message, timezone_selection_msg
from utils.censorship.checker import censor_load
from utils.fsm import State
from utils.scheduler import Scheduler

bot = AsyncTeleBot(token, parse_mode='HTML' )
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

def error_handler(func: Callable) -> Callable:
    """Декоратор для перехвата и логирования исключений в хэндлерах с отправкой пользователю сообщения об ошибке."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        """Внутренняя обёрточная функция декоратора: вызывает хэндлер и обрабатывает исключения."""
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
async def start(message: telebot.types.Message) -> None:
    """Обрабатывает команду /start: регистрирует пользователя и показывает главное меню или выбор часового пояса."""
    State.clear_state(message.chat.id)
    user_is_admin = await is_admin(message.chat.id)
    if await is_user_banned(message.chat.id):
        await bot.send_message(message.chat.id, banned_msg)
        return
    logging.info(f"Пользователь {message.chat.id} запустил бота")
    if is_owner(message.chat.id):
        await add_user(message.chat.id, message.from_user.username,
                       'Owner')

    else:

        await add_user(message.chat.id, message.from_user.username,
                       f"{'Admin' if user_is_admin else 'User'}")
    if await get_timezone(message.chat.id) is not None:
        await bot.send_message(
            message.chat.id,
            start_message(message.from_user.first_name),
            reply_markup=main_menu(message.chat.id, user_is_admin)
        )
    else:
        await bot.send_message(message.chat.id,
                               timezone_selection_msg(
                                   message.from_user.first_name),
                               reply_markup=timezone_selection_keyboard()
                               )


@bot.message_handler(content_types=['text'], func=lambda msg: State.user_states.get(msg.chat.id) is not None)
async def state_handler(message: telebot.types.Message) -> None:
    """Обрабатывает сообщения в состоянии FSM."""
    await handle_fsm_text(message, bot)


@bot.message_handler(content_types=['photo'], func=lambda msg: State.user_states.get(msg.chat.id))
async def handle_photo_with_state(message: telebot.types.Message) -> None:
    """Обрабатывает фотографии в состоянии FSM."""
    await handle_fsm_photo(message, bot)


@bot.message_handler(content_types=['video', 'animation'], func=lambda msg: State.user_states.get(msg.chat.id))
async def handle_video_with_state(message: telebot.types.Message) -> None:
    """Обрабатывает видео и анимации в состоянии FSM."""
    await handle_fsm_video(message, bot)


@bot.message_handler(content_types=['text'])
# @error_handler
async def msg(message: telebot.types.Message) -> None:
    """Обрабатывает обычные текстовые сообщения."""
    await update_username(message.chat.id, message.from_user.username, bot)
    await update_user_activity_smart(message.chat.id)
    await handle_main_message(message, bot)


@bot.callback_query_handler(func=lambda call: True)
@error_handler
async def callback_inline(call: telebot.types.CallbackQuery) -> None:
    """Диспетчер всех callback-запросов бота: разбирает call.data и вызывает соответствующий хэндлер."""
    if await is_user_banned(call.message.chat.id):
        await bot.answer_callback_query(call.id, "🚫 Ваш аккаунт заблокирован.", show_alert=True)
        return
    await update_user_activity_smart(call.message.chat.id)
    await route_callback(call, bot)



async def start_bot() -> None:
    """Инициализирует базу данных, запускает планировщик напоминаний и запускает бота."""
    await init_db()
    reminder_service = Scheduler(bot)
    await reminder_service.start()
    await censor_load()

    # Получаем текущий цикл событий для регистрации обработчиков сигналов
    loop = asyncio.get_event_loop()

    # Функция для остановки бота
    def stop_bot_handler():
        logging.info('Получен сигнал выключения, завершаю работу бота...')
        bot.stop_polling()

    # Регистрируем обработчик сигналов через asyncio
    try:
        loop.add_signal_handler(signal.SIGINT, stop_bot_handler)
        loop.add_signal_handler(signal.SIGTERM, stop_bot_handler)
    except:
        pass

    try:
        while True:
            try:
                logging.info("Бот запущен")
                await bot.infinity_polling()
                # Если бот завершился нормально (после stop_bot()), выходим
                break
            except (ReadTimeout, ConnectionError, telebot.apihelper.ApiException) as e:
                logging.error(f"Произошла ошибка: {e}. Перезапуск через 15 секунд...")
                await asyncio.sleep(15)
            except KeyboardInterrupt:
                logging.info('Получен сигнал прерывания (KeyboardInterrupt)')
                bot.stop_polling()
                break
    finally:
        # Гарантированное закрытие ресурсов
        logging.info('Остановка напоминаний...')
        try:
            await reminder_service.stop()
        except Exception as e:
            logging.error(f"Ошибка при остановке напоминаний: {e}")

        logging.info('Закрытие сессии бота...')
        try:
            # Закрыть aiohttp сессию
            if hasattr(bot, 'session_manager') and bot.session_manager:
                await bot.session_manager.session.close()
        except Exception as e:
            logging.error(f"Ошибка при закрытии сессии: {e}")

        logging.info('Бот успешно остановлен')


if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logging.info('Главный процесс прерван')
    except Exception as e:
        logging.error(f"Критическая ошибка при запуске: {e}", exc_info=True)

