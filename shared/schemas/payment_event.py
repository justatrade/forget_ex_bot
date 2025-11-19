from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel

class PaymentEvent(BaseModel):
    payment_id: int
    user_id: int
    status: str = "pending"
    amount: Optional[int] = None
    currency: Optional[str] = "RUB"
    paid_at: Optional[datetime] = None
    meta: Optional[dict[str, Any]] = None
