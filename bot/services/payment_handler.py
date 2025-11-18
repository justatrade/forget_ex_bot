from shared.config import setup_logger
from bot.services.channel_service import ChannelService
from bot.schemas.payment_event import PaymentEvent

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
