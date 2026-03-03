"""
Утилита для работы с медиа-каналом Telegram.
Сохраняет фото/видео в канал и обеспечивает fallback при отправке.
"""
import logging

from config import media_storage_channel_id

_logger = logging.getLogger(__name__)


async def save_media_to_channel(bot, file_id, media_type='photo'):
    """
    Сохраняет медиафайл в канал хранения.

    Args:
        bot: Экземпляр бота
        file_id: ID файла для сохранения
        media_type: Тип медиа ('photo', 'video' или 'animation')

    Returns:
        tuple: (channel_message_id, new_file_id) или (None, file_id) при ошибке
    """
    try:
        if media_type == 'photo':
            sent_message = await bot.send_photo(
                chat_id=media_storage_channel_id,
                photo=file_id
            )
            # Получаем новый file_id из отправленного сообщения
            new_file_id = sent_message.photo[-1].file_id
        elif media_type == 'video':
            sent_message = await bot.send_video(
                chat_id=media_storage_channel_id,
                video=file_id
            )
            if sent_message.video:
                new_file_id = sent_message.video.file_id
            elif sent_message.animation:
                new_file_id = sent_message.animation.file_id
                media_type = 'animation'
            else:
                _logger.error("Не удалось определить тип отправленного видео")
                return None, file_id
        elif media_type == 'animation':
            sent_message = await bot.send_animation(
                chat_id=media_storage_channel_id,
                animation=file_id
            )
            new_file_id = sent_message.animation.file_id
        else:
            _logger.error(f"Неподдерживаемый тип медиа: {media_type}")
            return None, file_id

        _logger.info(f"Медиафайл {media_type} сохранен в канал. Message ID: {sent_message.message_id}")
        return sent_message.message_id, new_file_id

    except Exception as e:
        _logger.error(f"Ошибка при сохранении медиа в канал: {e}")
        return None, file_id


async def send_media_with_fallback(bot, chat_id, file_id, channel_message_id,
                                   media_type='photo', caption=None, reply_markup=None,
                                   update_callback=None):
    """
    Отправляет медиафайл с fallback механизмом.

    Сначала пытается отправить по file_id.
    Если не получается - пересылает из канала и обновляет file_id через callback.

    Args:
        bot: Экземпляр бота
        chat_id: ID чата получателя
        file_id: Текущий file_id
        channel_message_id: ID сообщения в канале хранения (может быть None)
        media_type: Тип медиа ('photo', 'video' или 'animation')
        caption: Подпись к медиа
        reply_markup: Клавиатура
        update_callback: Async функция для обновления file_id в БД
                        Должна принимать новый file_id как аргумент

    Returns:
        Отправленное сообщение или None при ошибке
    """

    # Сначала пробуем отправить по file_id
    try:
        if media_type == 'photo':
            sent_message = await bot.send_photo(
                chat_id=chat_id,
                photo=file_id,
                caption=caption,
                reply_markup=reply_markup
            )
        elif media_type == 'video':
            sent_message = await bot.send_video(
                chat_id=chat_id,
                video=file_id,
                caption=caption,
                reply_markup=reply_markup
            )
        elif media_type == 'animation':
            sent_message = await bot.send_animation(
                chat_id=chat_id,
                animation=file_id,
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            _logger.error(f"Неподдерживаемый тип медиа: {media_type}")
            return None

        _logger.debug("Медиа отправлено по file_id успешно")
        return sent_message

    except Exception as e:
        _logger.warning(f"Не удалось отправить медиа по file_id: {e}. Пробуем через канал...")

        if media_type == 'video':
            try:
                sent_message = await bot.send_animation(
                    chat_id=chat_id,
                    animation=file_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
                _logger.debug("Медиа отправлено по file_id как animation")
                return sent_message
            except Exception:
                pass

        # Если не удалось отправить по file_id, пробуем через канал
        if not channel_message_id:
            _logger.error("channel_message_id отсутствует, невозможно получить медиа из канала")
            return None

        try:
            # Копируем сообщение из канала
            copied_message = await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=media_storage_channel_id,
                message_id=channel_message_id,
                caption=caption,
                reply_markup=reply_markup
            )

            # Получаем актуальное сообщение из канала для извлечения нового file_id
            channel_message = await bot.forward_message(
                chat_id=chat_id,
                from_chat_id=media_storage_channel_id,
                message_id=channel_message_id
            )

            # Удаляем пересланное сообщение (оно нам не нужно, мы уже скопировали)
            try:
                await bot.delete_message(chat_id, channel_message.message_id)
            except Exception:
                pass

            # Извлекаем новый file_id
            if media_type == 'photo' and channel_message.photo:
                new_file_id = channel_message.photo[-1].file_id
            elif media_type in ('video', 'animation'):
                if channel_message.video:
                    new_file_id = channel_message.video.file_id
                elif channel_message.animation:
                    new_file_id = channel_message.animation.file_id
                    media_type = 'animation'
                else:
                    _logger.error("Не удалось извлечь file_id из сообщения канала")
                    return copied_message
            else:
                _logger.error("Не удалось извлечь file_id из сообщения канала")
                return copied_message

            # Обновляем file_id в БД, если передан callback
            if update_callback:
                try:
                    await update_callback(new_file_id)
                    _logger.info(f"file_id обновлен в БД: {new_file_id}")
                except Exception as update_error:
                    _logger.error(f"Ошибка при обновлении file_id в БД: {update_error}")

            _logger.info("Медиа отправлено через канал и file_id обновлен")
            return copied_message

        except Exception as fallback_error:
            _logger.error(f"Ошибка при отправке медиа через канал: {fallback_error}")
            return None
