from typing import Optional

from telebot.async_telebot import AsyncTeleBot
from telebot.types import ChatInviteLink

from shared.config import settings, setup_logger
from shared.schemas import CHANNEL_ID_TO_FIELD_MAP, DashaChannelPresence

logger = setup_logger(__name__)


class ChannelService:
    _bot: AsyncTeleBot = None

    @classmethod
    def set_bot(cls, bot: AsyncTeleBot):
        """Устанавливает экземпляр бота для использования в сервисе"""
        cls._bot = bot
        logger.info("Bot instance set for ChannelService")

    @classmethod
    async def grant_access(
            cls, telegram_id: int, channel_id: Optional[int] = None
    ) -> str:
        """
        Даёт доступ пользователю к каналу.
        Пытается добавить напрямую, если не получается - создаёт одноразовую ссылку.
        Возвращает инвайт-ссылку или сообщение об успехе.
        """
        if not cls._bot:
            logger.error("Bot instance not set in ChannelService")
            raise RuntimeError("Bot instance not initialized")

        if not channel_id:
            channel_id = settings.channel.get_channel_id(settings.app.debug)

        try:
            invite_link: ChatInviteLink = (
                await cls._bot.create_chat_invite_link(
                    chat_id=channel_id,
                    member_limit=1,
                    name=f"User_{telegram_id}"
                )
            )

            logger.info(
                "Invite link created for user "
                f"{telegram_id}: {invite_link.invite_link}"
            )

            return invite_link.invite_link

        except Exception as invite_error:
            logger.error(
                "Failed to create invite link for "
                f"user {telegram_id}: {invite_error}"
            )
            raise

    @classmethod
    async def send_notification(cls, telegram_id, message: str):
        await cls._bot.send_message(
            telegram_id,
            message,
        )

    @classmethod
    async def revoke_access(
            cls, telegram_id: int, channel_id: Optional[int] = None
    ):
        """Забирает доступ у пользователя (бан в канале)"""
        if not cls._bot:
            logger.error("Bot instance not set in ChannelService")
            raise RuntimeError("Bot instance not initialized")

        if not channel_id:
            channel_id = settings.channel.get_channel_id(settings.app.debug)

        try:
            await cls._bot.ban_chat_member(channel_id, telegram_id)
            logger.info(f"User {telegram_id} banned from channel")
        except Exception as e:
            logger.error(f"Failed to ban user {telegram_id}: {e}")
            raise

    @classmethod
    async def check_user_presence(cls, user_tg_id: int) -> DashaChannelPresence:
        user_presence = DashaChannelPresence()

        for channel_id, field_name in CHANNEL_ID_TO_FIELD_MAP.items():
            if not hasattr(user_presence, field_name):
                continue
            try:
                user = await cls._bot.get_chat_member(channel_id, user_tg_id)
                setattr(
                    user_presence,
                    field_name,
                    user.status in (
                        "member",
                        "creator",
                        "administrator",
                        "restricted",
                    )
                )
            except Exception as error:
                logger.error(
                    f"Failed to check presence for user {user_tg_id}: {error}"
                )

        return user_presence
