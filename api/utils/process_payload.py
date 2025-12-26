from fastapi import HTTPException, Request

from pydantic import ValidationError

from api.services import RobokassaPaymentService
from shared.config import setup_logger
from shared.database.models import PaymentStatus
from shared.schemas import RobokassaResult
from shared.services import RedisStreamPublisher, RobokassaService


logger = setup_logger(__name__)


async def handle_robokassa_payload(
        request: Request,
        publisher: RedisStreamPublisher,
        payment_status: PaymentStatus,
):
    try:
        payload = RobokassaResult.model_validate(request.query_params)
    except ValidationError as e:
        logger.warning(f"Robokassa validation error: {e.errors()}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    if not RobokassaService.check_signature(payload):
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug(f"Processing Robokassa payment with payload: {payload}")
    await RobokassaPaymentService.process_payment(
        payload, publisher, payment_status
    )

    return payload
