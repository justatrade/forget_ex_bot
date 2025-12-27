from fastapi import HTTPException, Request

from pydantic import ValidationError

from api.services import RobokassaPaymentService
from shared.config import settings, setup_logger
from shared.database.models import PaymentStatus
from shared.schemas import ReturnUrl ,RobokassaResult
from shared.services import RedisStreamPublisher, RobokassaService


logger = setup_logger(__name__)


async def handle_robokassa_payload(
        request: Request,
        publisher: RedisStreamPublisher,
        payment_status: PaymentStatus,
        return_url: ReturnUrl,
):
    try:
        payload = RobokassaResult.model_validate(request.query_params)
    except ValidationError as e:
        logger.warning(f"Robokassa validation error: {e.errors()}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    if return_url in (ReturnUrl.success, ReturnUrl.fail):
        password = settings.rk.password_1
    elif return_url == ReturnUrl.result:
        password = settings.rk.password_2
    else:
        raise HTTPException(status_code=400, detail="Unknown return_url")

    if not RobokassaService.check_signature(payload, password):
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug(f"Processing Robokassa payment with payload: {payload}")
    await RobokassaPaymentService.process_payment(
        payload, publisher, payment_status
    )

    return payload
