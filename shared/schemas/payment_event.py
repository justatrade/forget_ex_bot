from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, field_validator

from shared.database.models import PaymentStatus


class PaymentEvent(BaseModel):
    payment_id: int
    user_id: int
    status: PaymentStatus = PaymentStatus.PENDING
    amount: Optional[int] = None
    currency: Optional[str] = "RUB"
    paid_at: Optional[datetime] = None
    meta: Optional[dict[str, Any]] = None


class RobokassaResult(BaseModel):
    OutSum: str
    InvId: int
    SignatureValue: str
    IsTest: int = 0
    Culture: str = "ru"

    @field_validator("OutSum", mode="before")
    @staticmethod
    def convert(v):
        if isinstance(v, str):
            return v
        return f"{v:.2f}"


class ProdamusPayment(PaymentEvent):
    pass


class RobokassaPayment(PaymentEvent, RobokassaResult):
    pass
