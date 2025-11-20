from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.services.channel_service import ChannelService
from shared.config import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import User
from shared.schemas import PaymentEvent

logger = setup_logger(__name__)


class PaymentHandler:
    """
    Обрабатывает события об оплате.
    Сейчас — минимальная версия:
    - десериализация данных
    - вызов ChannelService.grant_access
    """

    @staticmethod
    async def process(event: PaymentEvent) -> None:
        """
        Основной метод обработки.
        Здесь будет расширение логики (retry, идемпотентность, db-транзакции и т.п.)
        """

        telegram_id = event.user_id

        logger.info(
            f"[PaymentHandler] Processing payment for user={telegram_id}"
        )

        try:
            result = await ChannelService.grant_access(telegram_id)
            async with DatabaseConnection.get_session() as session:
                session: AsyncSession

                user_result = await session.execute(
                    select(User)
                    .options(selectinload(User.payments))
                    .filter(User.telegram_id == telegram_id)
                )
                user: User = user_result.scalar_one_or_none()

                user.invite_link = result

            logger.info(
                f"[PaymentHandler] Access granted to user={telegram_id}, "
                f"result={result}"
            )
        except Exception as e:
            logger.error(
                "[PaymentHandler] Failed to process event for "
                f"user={telegram_id}: {e}"
            )
            raise
