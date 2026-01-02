import asyncio

from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import StateFilter
from telebot.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)

from bot.utils.states import Notify
from bot.utils.messages import WAITING_FOR_MEDIA_MESSAGE
from shared.config import settings, setup_logger
from shared.database.models import User
from shared.database.repository import get_users_who_started_but_did_not_payed


logger = setup_logger(__name__)


async def cmd_send_notification(msg: Message, bot: AsyncTeleBot) -> None:
    await bot.set_state(
        msg.from_user.id, Notify.waiting_for_media, msg.chat.id
    )
    await bot.send_message(
        msg.chat.id,
        WAITING_FOR_MEDIA_MESSAGE,
    )


async def receive_media_for_notification(msg: Message, bot: AsyncTeleBot) -> None:
    user_id = msg.from_user.id
    chat_id = msg.chat.id

    caption = msg.caption or ""

    if msg.video_note:
        media_type = "video_note"
        file_id = msg.video_note.file_id
    elif msg.video:
        media_type = "video"
        file_id = msg.video.file_id
    elif msg.voice:
        media_type = "voice"
        file_id = msg.voice.file_id
    elif msg.photo:
        media_type = "photo"
        file_id = msg.photo[-1].file_id
    elif msg.document:
        media_type = "document"
        file_id = msg.document.file_id
    elif msg.sticker:
        media_type = "sticker"
        file_id = msg.sticker.file_id
    elif msg.audio:
        media_type = "audio"
        file_id = msg.audio.file_id
    elif msg.text:
        media_type = "text"
        file_id = None
    else:
        await bot.send_message(
            chat_id,
            text="❌ Поддерживаются: кружки, видео, аудио, фото, документы. "
                 "Попробуйте ещё раз."
        )
        return

    try:
        await bot.forward_message(chat_id, chat_id, msg.message_id)
    except Exception:
        if media_type == "video_note":
            await bot.send_video_note(chat_id, file_id)
        elif media_type == "voice":
            await bot.send_voice(chat_id, file_id, caption=caption)
        elif media_type == "video":
            await bot.send_video(chat_id, file_id, caption=caption)
        elif media_type == "photo":
            await bot.send_photo(chat_id, file_id, caption=caption)
        elif media_type == "document":
            await bot.send_document(chat_id, file_id, caption=caption)

    n_recipients = await get_users_who_started_but_did_not_payed()

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(
            text="✅ Отправить",
            callback_data="notify_confirm",
        ),
        InlineKeyboardButton(
            text="❌ Отменить",
            callback_data="notify_cancel",
        )
    )

    message = await bot.send_message(
        chat_id,
        text=f"📤 Это сообщение будет отправлено "
             f"<b>{len(n_recipients)}</b> пользователям.\n"
             f"Тип: <code>{media_type}</code>",
        reply_markup=markup,
        parse_mode="HTML"
    )
    async with bot.retrieve_data(user_id, chat_id) as data:
        data["media_type"] = media_type
        data["file_id"] = file_id
        data["caption"] = caption
        data["message_id"] = message.message_id

    await bot.set_state(user_id, Notify.preview_confirmed, chat_id)


async def handle_notify_confirmation(call: CallbackQuery, bot: AsyncTeleBot) -> None:
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    async with bot.retrieve_data(user_id, chat_id) as data:
        media_type = data.get("media_type")
        file_id = data.get("file_id")
        message_id = data.get("message_id")

    if call.data == "notify_cancel":
        await bot.delete_state(user_id, chat_id)
        await bot.answer_callback_query(call.id, "❌ Отменено")
        await bot.edit_message_text(
            "🚫 Отправка отменена.",
            chat_id, call.message.message_id
        )
        return

    if call.data == "notify_confirm":
        if not media_type or not file_id:
            await bot.answer_callback_query(
                call.id,
                text="⚠️ Данные устарели",
                show_alert=True,
            )

            return

        await bot.answer_callback_query(
            call.id,
            text="✅ Отправляю!",
        )

        if await send_notification_to_users(bot, user_id, chat_id):
            await bot.edit_message_text(
                "📤 Уведомление отправлено!",
                chat_id,
                message_id,
            )
            await bot.delete_state(user_id, chat_id)
        else:
            await bot.edit_message_text(
                "Что-то пошло не так",
                chat_id,
                message_id,
            )


async def cmd_cancel_state(msg: Message, bot: AsyncTeleBot) -> None:
    current_state = await bot.get_state(msg.from_user.id, msg.chat.id)
    print(current_state)
    await bot.delete_state(msg.from_user.id, msg.chat.id)
    await bot.send_message(msg.chat.id, "❌ Операция отменена.")


async def send_notification_to_users(
        bot: AsyncTeleBot,
        admin_user_id: int,
        admin_chat_id: int,
) -> bool:
    async with bot.retrieve_data(admin_user_id, admin_chat_id) as data:
        media_type: str = data.get("media_type")
        file_id: str = data.get("file_id")
        caption: str = data.get("caption")
        if not media_type or not file_id:
            logger.error(
                f"State data is incomplete. media_type {media_type} "
                f"and file_id {file_id}"
            )
            raise ValueError("State data is incomplete")

    users = await get_users_who_started_but_did_not_payed()
    success_count = 0
    for user in users:
        try:
            if media_type == "video_note":
                await bot.send_video_note(user.telegram_id, file_id)
            elif media_type == "voice":
                await bot.send_voice(
                    user.telegram_id, file_id, caption=caption
                )
            elif media_type == "video":
                await bot.send_video(
                    user.telegram_id, file_id, caption=caption
                )
            elif media_type == "photo":
                await bot.send_photo(
                    user.telegram_id, file_id, caption=caption
                )
            elif media_type == "document":
                await bot.send_document(
                    user.telegram_id, file_id, caption=caption
                )
            elif media_type == "audio":
                await bot.send_audio(
                    user.telegram_id, file_id, caption=caption
                )
            elif media_type == "sticker":
                await bot.send_sticker(user.telegram_id, file_id)
            elif media_type == "text":
                await bot.send_message(user.telegram_id, file_id)
            else:
                raise ValueError(f"Unknown media type: {media_type}")
            success_count += 1
        except ValueError:
            logger.error(
                f"Incorrect media type. Stop sending notifications. "
                f"{success_count} total sent"
            )
            return False
        except Exception as e:
            logger.warning(f"Failed to send to {user.telegram_id}: {e}")
        finally:
            await asyncio.sleep(0.3)

    logger.info(f"Notification sent to {success_count}/{len(users)} users")
    return True


def register_handlers(bot: AsyncTeleBot):
    bot.add_custom_filter(StateFilter(bot))

    bot.register_message_handler(
        lambda msg: receive_media_for_notification(msg, bot),
        content_types=[
            "text",
            "video",
            "audio",
            "video_note",
            "voice",
            "sticker",
            "text,"
        ],
        func=lambda msg: msg.from_user.id in settings.telegram.admin_id,
        state=Notify.waiting_for_media.name,
        pass_bot=True,
        chat_types=["private"],
    )
    bot.register_callback_query_handler(
        lambda call: handle_notify_confirmation(call, bot),
        func=lambda call: call.data in ["notify_confirm", "notify_cancel"],
        state=Notify.preview_confirmed,
        pass_bot=True,
    )

    bot.register_message_handler(
        lambda msg: cmd_send_notification(msg, bot),
        func=lambda msg: msg.from_user.id in settings.telegram.admin_id,
        pass_bot=True,
        chat_types=["private"],
        commands=["notify_not_buying"],
    )

    bot.register_message_handler(
        lambda msg: cmd_cancel_state(msg, bot),
        func=lambda msg: msg.from_user.id in settings.telegram.admin_id,
        commands=["cancel"],
        pass_bot=True,
        chat_types=["private"],
    )
