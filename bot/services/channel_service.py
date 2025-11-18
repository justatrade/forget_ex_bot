from telebot.async_telebot import AsyncTeleBot
from telebot.types import ChatInviteLink
from shared.config import settings
from shared.config import setup_logger
from bot.utils.messages import (
    CHANNEL_INVITE_LINK_MESSAGE,
    PAYMENT_SUCCESS_MESSAGE,
)

logger = setup_logger(__name__)


class ChannelService:
    _bot: AsyncTeleBot = None

    @classmethod
    def set_bot(cls, bot: AsyncTeleBot):
        """Устанавливает экземпляр бота для использования в сервисе"""
        cls._bot = bot
        logger.info("Bot instance set for ChannelService")

    @classmethod
    async def grant_access(cls, telegram_id: int) -> str:
        """
        Даёт доступ пользователю к каналу.
        Пытается добавить напрямую, если не получается - создаёт одноразовую ссылку.
        Возвращает инвайт-ссылку или сообщение об успехе.
        """
        if not cls._bot:
            logger.error("Bot instance not set in ChannelService")
            raise RuntimeError("Bot instance not initialized")

        channel_id = settings.channel.get_channel_id(settings.app.debug)

        try:
            await cls._bot.unban_chat_member(channel_id, telegram_id)
            logger.info(f"User {telegram_id} added to channel directly")

            await cls._bot.send_message(
                telegram_id,
                PAYMENT_SUCCESS_MESSAGE.format(channel_link="")
            )

            return "direct_add"

        except Exception as e:
            logger.warning(
                f"Could not add user {telegram_id} directly: {e}. "
                "Creating invite link..."
            )

            try:
                invite_link: ChatInviteLink = await cls._bot.create_chat_invite_link(
                    chat_id=channel_id,
                    member_limit=1,
                    name=f"User_{telegram_id}"
                )

                logger.info(f"Invite link created for user {telegram_id}: {invite_link.invite_link}")

                await cls._bot.send_message(
                    telegram_id,
                    PAYMENT_SUCCESS_MESSAGE.format(
                        channel_link=CHANNEL_INVITE_LINK_MESSAGE.format(
                            channel_link=invite_link.invite_link
                        )
                    )
                )

                return invite_link.invite_link

            except Exception as invite_error:
                logger.error(f"Failed to create invite link for user {telegram_id}: {invite_error}")
                raise

    @classmethod
    async def revoke_access(cls, telegram_id: int):
        """Забирает доступ у пользователя (бан в канале)"""
        if not cls._bot:
            logger.error("Bot instance not set in ChannelService")
            raise RuntimeError("Bot instance not initialized")

        channel_id = settings.channel.get_channel_id(settings.app.debug)

        try:
            await cls._bot.ban_chat_member(channel_id, telegram_id)
            logger.info(f"User {telegram_id} banned from channel")
        except Exception as e:
            logger.error(f"Failed to ban user {telegram_id}: {e}")
            raise