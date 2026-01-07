from sqlalchemy import select

from shared.database.connection import DatabaseConnection
from shared.database.models import User, Payment, PaymentStatus, PaymentSystem


EXCLUDED_USER_IDS = {1, 2, 3, 4, 5}


async def get_users_who_started_but_did_not_payed() -> list[User]:
    async with (DatabaseConnection.get_session() as session):
        successful_payment_exists = (
            select(Payment.user_id)
            .where(
                Payment.user_id == User.id,
                Payment.payment_system == PaymentSystem.ROBOKASSA,
                Payment.status == PaymentStatus.SUCCESS,
            )
            .exists()
        )

        stmt = (
            select(User)
            .where(
                ~successful_payment_exists,
                User.id.not_in(EXCLUDED_USER_IDS),
            )
        )

        result = await session.execute(stmt)
        return list(result.scalars())
