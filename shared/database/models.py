from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, Date, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer
from datetime import datetime, UTC
import enum
import re


@as_declarative()
class BaseModel:
    id: int = Column(Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def __tablename__(cls):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


class UserStatus(enum.Enum):
    NEW = "new"
    INTERESTED = "interested"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"


class User(BaseModel):
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.NEW)
    payment_status = Column(Boolean, default=False)
    created_at = Column(DateTime)
    last_interaction = Column(DateTime, onupdate=datetime.now(UTC))
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_72h_sent = Column(Boolean, default=False)

    payments = relationship("Payment", back_populates="user")
    insult_usage = relationship("InsultUsage", back_populates="user")


class Payment(BaseModel):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    order_id = Column(String, unique=True, nullable=False)
    amount = Column(Integer, nullable=False)
    promo_code = Column(String, nullable=True)
    status = Column(String, default="pending")
    prodamus_payment_id = Column(String, nullable=True)
    created_at = Column(DateTime)
    paid_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")


class PromoCode(BaseModel):
    code = Column(String, unique=True, nullable=False, index=True)
    discount_percent = Column(Integer, nullable=True)
    discount_fixed = Column(Integer, nullable=True)
    final_price = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime)


class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class Insult(BaseModel):
    gender = Column(Enum(GenderEnum), nullable=False)
    text = Column(Text, nullable=False)
    media_type = Column(String, nullable=True)
    media_path = Column(String, nullable=True)
    created_at = Column(DateTime)


class InsultUsage(BaseModel):
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    date = Column(Date)
    count = Column(Integer, default=0)

    user = relationship("User", back_populates="insult_usage")