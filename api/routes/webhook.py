from datetime import datetime

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from bot.services import ProdamusService
from bot.services import ChannelService
from shared.config.logger import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import Payment, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = setup_logger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.post("/")
async def prodamus_webhook(request: Request):
    """Обработка webhook от Prodamus после оплаты"""

    reply = {}
    try:
        data = await request.form()
        data_dict = dict(data)

        logger.info(
            f"Received webhook from Prodamus: {data_dict.get('order_id')}"
        )

        received_signature = data_dict.get("signature")
        if not received_signature:
            logger.error("No signature in webhook")
            raise HTTPException(status_code=400, detail="No signature")

        is_valid = await ProdamusService.verify_webhook_signature(
            data_dict, received_signature
        )
        if not is_valid:
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=403, detail="Invalid signature")

        order_id = data_dict.get("order_id")
        payment_status = data_dict.get("payment_status")

        if payment_status != "success":
            logger.warning(
                f"Payment not successful: {order_id}, status: {payment_status}"
            )
            reply = {"status": "ok", "message": "Payment not successful"}

        async with DatabaseConnection.get_session() as session:
            session: AsyncSession

            result = await session.execute(
                select(Payment).filter(Payment.order_id == order_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error(f"Payment not found: {order_id}")
                raise HTTPException(status_code=404, detail="Payment not found")

            if payment.status == "success":
                logger.info(f"Payment already processed: {order_id}")
                reply = {"status": "ok", "message": "Already processed"}

            payment.status = "success"
            payment.paid_at = datetime.now()
            payment.prodamus_payment_id = data_dict.get("payment_id")

            user_result = await session.execute(
                select(User).filter(User.id == payment.user_id)
            )
            user = user_result.scalar_one_or_none()

            if user:
                user.payment_status = True
                user.status = "paid"

                try:
                    await ChannelService.grant_access(user.telegram_id)
                    logger.info(f"Access granted to user {user.telegram_id}")
                except Exception as e:
                    logger.error(
                        "Failed to grant access to user "
                        f"{user.telegram_id}: {e}"
                    )

        logger.info(f"Payment processed successfully: {order_id}")
        if not reply:
            reply = {"status": "ok", "message": "Payment processed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    else:
        return JSONResponse(content=reply, status_code=200)
