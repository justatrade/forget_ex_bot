from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.utils.dependencies import get_publisher
from shared.config import setup_logger
from shared.config import settings
from shared.database.connection import DatabaseConnection
from shared.database.models import Payment, User, UserStatus
from shared.schemas import PaymentEvent
from shared.services import ProdamusService, RedisStreamPublisher


logger = setup_logger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])


@router.api_route("/success", methods=["GET", "POST"])
@router.api_route("", methods=["GET", "POST"])
async def prodamus_webhook(
    request: Request,
    publisher: RedisStreamPublisher = Depends(get_publisher)
):
    """Обработка webhook от Prodamus после оплаты"""

    reply = {}
    try:
        if request.method == "POST":
            data = await request.form()
        elif request.method == "GET":
            data = request.query_params
        else:
            logger.error("Unsupported method")
            raise HTTPException(status_code=405, detail="Method not allowed")

        data_dict = dict(data)

        logger.info(
            "Received webhook from Prodamus: "
            f"{data_dict.get(
                settings.prodamus.var_prefix+'order_id',
                data_dict.get('order_num'),
            )}"
        )

        received_signature = data_dict.get(
            settings.prodamus.var_prefix + "sign",
            data_dict.get("sign"),
        )
        if not received_signature:
            received_signature = request.headers.get("Sign")
            data_dict.update({"sign": received_signature})
        if not received_signature:
            logger.error(
                "No signature in webhook. "
                f"Data: {data_dict}. Header: {request.headers}"
            )
            raise HTTPException(status_code=400, detail="No signature")

        is_valid = await ProdamusService.verify_webhook_signature(data_dict)
        if not is_valid:
            logger.error(f"Invalid webhook signature. Data: {data_dict}")
            raise HTTPException(status_code=403, detail="Invalid signature")

        order_id = data_dict.get(
            settings.prodamus.var_prefix + "order_id",
            data_dict.get("order_num"),
        )
        payment_status = data_dict.get(
            settings.prodamus.var_prefix + "status",
            data_dict.get("status"),
        )

        if payment_status != "success":
            logger.warning(
                f"Payment not successful: {order_id}, status: {payment_status}."
                f"Data: {data_dict}"
            )
            reply = {"status": "ok", "message": "Payment not successful"}
            return JSONResponse(content=reply, status_code=200)

        async with DatabaseConnection.get_session() as session:
            session: AsyncSession

            result = await session.execute(
                select(Payment)
                .options(selectinload(Payment.user))
                .filter(Payment.order_id == order_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error(
                    f"Payment not found: {order_id}. Data: {data_dict}"
                )
                raise HTTPException(status_code=404, detail="Payment not found")

            if payment.status == "success":
                logger.info(
                    f"Payment already processed: {order_id}. Data: {data_dict}"
                )
                reply = {"status": "ok", "message": "Already processed"}
                return JSONResponse(content=reply, status_code=200)
            else:
                payment.status = payment_status
                payment.prodamus_payment_id = data_dict.get(
                    settings.prodamus.var_prefix + "id",
                    data_dict.get("order_id"),
                )

            if payment_status == "success":
                payment.paid_at = datetime.now()

                user_result = await session.execute(
                    select(User)
                    .options(selectinload(User.payments))
                    .filter(User.id == payment.user_id)
                )
                user = user_result.scalar_one_or_none()

                if user:
                    user.payment_status = True
                    user.status = UserStatus.PAID

                    event = PaymentEvent(
                        payment_id=payment.id,
                        user_id=user.telegram_id,
                        status=payment_status,
                        paid_at=datetime.now(),
                    )

                    msg_id = await publisher.publish(event)
                    logger.info(f"PaymentEvent sent to Redis Stream: {msg_id}")

        logger.info(f"Payment processed successfully: {order_id}")
        if not reply:
            reply = {"status": "ok", "message": "Payment processed"}
            return JSONResponse(content=reply, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        await publisher.publish(event, settings.redis.dlq_stream)
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
    else:
        return JSONResponse(content=reply, status_code=200)
