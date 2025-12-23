from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.services.channel_service import ChannelService
from bot.utils.messages import (
    CHANNEL_INVITE_LINK_MESSAGE,
    PAYMENT_SUCCESS_MESSAGE,
)
from shared.config import setup_logger, settings
from shared.database.connection import DatabaseConnection
from shared.database.models import Payment, User
from shared.schemas import CHANNEL_FIELD_TO_ID_MAP, PaymentEvent

logger = setup_logger(__name__)


class PaymentHandler:
    """
    Обрабатывает события об оплате.
    Сейчас — минимальная версия:
    - десериализация данных
    - вызов ChannelService.grant_access
    """
    async def process(self, event: PaymentEvent) -> None:
        """
        Роутер по разным флоу, в зависимости от режима продаж
        :param event:
        :return:
        """
        telegram_id = event.user_id

        logger.info(
            f"[PaymentHandler] Processing payment for user={telegram_id}"
        )

        if settings.telegram.sell_mode == "Dasha":
            await self.process_dasha(event)
        elif settings.telegram.sell_mode == "Dasha-Mara":
            await self.process_dasha_mara(event)
        else:
            return

    @staticmethod
    async def process_dasha_mara(event: PaymentEvent) -> None:
        """
        Основной метод обработки.
        Здесь будет расширение логики (retry, идемпотентность, db-транзакции и т.п.)
        """
        try:
            invite_link = await ChannelService.grant_access(event.user_id)
            notification = PAYMENT_SUCCESS_MESSAGE.format(
                channel_link=CHANNEL_INVITE_LINK_MESSAGE.format(
                    channel_link=invite_link
                )
            )
            await ChannelService.send_notification(event.user_id, notification)
            async with DatabaseConnection.get_session() as session:
                session: AsyncSession

                user_result = await session.execute(
                    select(User)
                    .options(selectinload(User.payments))
                    .filter(User.telegram_id == event.user_id)
                )
                user: User = user_result.scalar_one_or_none()

                user.invite_link = invite_link

            logger.info(
                f"[PaymentHandler] Access granted to user={event.user_id}, "
                f"result={invite_link}"
            )
        except Exception as e:
            logger.error(
                "[PaymentHandler] Failed to process event for "
                f"user={event.user_id}: {e}"
            )
            raise

    @staticmethod
    async def process_dasha(event: PaymentEvent) -> None:
        user_presence = await ChannelService.check_user_presence(event.user_id)

        async with DatabaseConnection.get_session() as session:
            session: AsyncSession

            user_result = await session.execute(
                select(User)
                .options(selectinload(User.payments))
                .filter(User.telegram_id == event.user_id)
            )
            user: User = user_result.scalar_one_or_none()
            payment_result = await session.execute(
                select(Payment)
                .filter(Payment.id == event.payment_id)
            )
            payment: Payment = payment_result.scalar_one_or_none()
            if payment.product == "all_special":
                channels = list(CHANNEL_FIELD_TO_ID_MAP.keys())
            else:
                channels = [payment.product]

            invite_links = []
            for channel in channels:
                if getattr(user_presence, channel):
                    logger.info(
                        f"[PaymentHandler] user={event.user_id} is already"
                        f"in channel {channel}"
                    )
                    continue
                try:
                    result = await ChannelService.grant_access(
                        event.user_id,
                        CHANNEL_FIELD_TO_ID_MAP[channel],
                    )
                    await ChannelService.send_notification(
                        event.user_id,
                        CHANNEL_INVITE_LINK_MESSAGE.format(channel_link=result)
                    )
                    invite_links.append(result)

                    logger.info(
                        f"[PaymentHandler] Access in channel {channel}"
                        f"granted to user={event.user_id}, "
                        f"result={result}"
                    )
                except Exception as e:
                    logger.error(
                        "[PaymentHandler] Failed to process event for "
                        f"user={event.user_id}: {e}, event={event}"
                    )
                    raise
            user.invite_link = ",".join(invite_links)
            await session.flush()
            await session.commit()
