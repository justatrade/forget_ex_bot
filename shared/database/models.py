from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    MetaData,
    String,
    Text,
)
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import mapped_column, relationship, Mapped
from sqlalchemy.types import Integer

import enum
import re
from datetime import date, datetime, UTC
from typing import Optional


@as_declarative()
class BaseModel:
    __abstract__ = True
    metadata: MetaData

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    @declared_attr
    def __tablename__(cls):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class UserStatus(enum.Enum):
    NEW = "new"
    INTERESTED = "interested"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"


class CameFrom(enum.Enum):
    MARA = "MARA"
    DASHA = "DASHA"
    BOTH = "BOTH"
    GUEST = "GUEST"

class User(BaseModel):
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus), default=UserStatus.NEW
    )
    payment_status: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_interaction: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.now()
    )
    invite_link: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    came_from: Mapped[CameFrom] = mapped_column(
        Enum(CameFrom), nullable=False, default=CameFrom.GUEST
    )

    payments: Mapped[list["Payment"]] = relationship(back_populates="user")
    insult_usage: Mapped[list["InsultUsage"]] = relationship(
        back_populates="user"
    )


class Payment(BaseModel):
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    order_id: Mapped[int] = mapped_column(String, unique=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    promo_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    prodamus_payment_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="payments")


class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"


class Insult(BaseModel):
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    media_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class InsultUsage(BaseModel):
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date)
    count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="insult_usage")
