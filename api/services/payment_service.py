from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.config import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import Payment, PaymentStatus, UserStatus
from shared.schemas import PaymentEvent, RobokassaResult
from shared.services import RedisStreamPublisher


logger = setup_logger(__name__)


class PaymentAbstractService(ABC):
    @abstractmethod
    async def process_payment(self, *args, **kwargs):
        pass


class PaymentService(PaymentAbstractService, ABC):
    @staticmethod
    async def get_payment(session: AsyncSession, order_id: int) -> Payment:
        result = await session.execute(
            select(Payment)
            .options(selectinload(Payment.user))
            .filter(Payment.order_id == str(order_id))
        )
        payment = result.scalar_one_or_none()

        return payment


class RobokassaPaymentService(PaymentService):
    @classmethod
    async def process_payment(
            cls,
            payload: RobokassaResult,
            publisher: RedisStreamPublisher,
            payment_status: PaymentStatus
    ) -> None:
        async with DatabaseConnection.get_session() as session:
            payment = await cls.get_payment(session, payload.InvId)

            if payment.status == PaymentStatus.SUCCESS:
                return

            payment.status = payment_status
            payment.external_payment_id = str(payload.InvId)
            payment.paid_at = datetime.now()

            if payment_status == PaymentStatus.SUCCESS:
                payment.user.payment_status = True
                payment.user.status = UserStatus.PAID
                event = PaymentEvent(
                    payment_id=payment.id,
                    amount=payload.OutSum,
                    user_id=payment.user.telegram_id,
                    status=payment_status,
                    paid_at=payment.paid_at,
                )

                msg_id = await publisher.publish(event)
                logger.info(f"PaymentEvent sent to Redis Stream: {msg_id}")
