import json
import re
from datetime import datetime
from hashlib import md5
from urllib import parse

import requests_async
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import settings
from shared.config import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import Payment, PaymentStatus, PaymentSystem, User
from shared.schemas import DashasSpecial, Goods, RobokassaResult


logger = setup_logger(__name__)


class RobokassaService:
    @staticmethod
    def _clean_text(text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(
            r"[^a-zA-Zа-яА-ЯёЁ0-9\s.,:;!?()\"\'\-/+=%\\]",
            "",
            text
        )

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    @staticmethod
    def _form_receipt(product: Goods) -> str:
        receipt_dict = {
            "items": [
                {
                    "name": RobokassaService._clean_text(product.name),
                    "quantity": 1,
                    "sum": product.price,
                    "tax": "none",
                }
            ]
        }
        return json.dumps(receipt_dict, ensure_ascii=False)

    @classmethod
    def check_signature(cls, result: RobokassaResult, password: str):
        signature = cls._calculate_signature(
            result.OutSum,
            result.InvId,
            password,
        )
        return signature == result.SignatureValue.lower()


    @staticmethod
    def _calculate_signature(*args) -> str:
        return md5(":".join(str(arg) for arg in args).encode()).hexdigest()

    @classmethod
    async def _get_resolved_payment_link(
            cls,
            user_tg_id: int,
            merchant_login: str,
            password_1: str,
            invoice_id: int,
            product: Goods,
            is_test: int = 0,
    ) -> str:
        data = {}
        price = product.price
        signature_args = [
            merchant_login,
            price,
            invoice_id,
            password_1,
        ]

        if settings.rk.receipt:
            receipt = RobokassaService._form_receipt(product)
            data.update({"Receipt": receipt})
            signature_args.insert(-1, receipt)

        signature = RobokassaService._calculate_signature(*signature_args)
        data.update(
            {
                "MerchantLogin": settings.rk.merchant_login,
                "OutSum": product.price,
                "InvoiceID": invoice_id,
                "Description": cls._clean_text(product.description),
                "SignatureValue": signature,
            }
        )
        data.update({"IsTest": is_test} if is_test else {})

        request_url = f"{settings.rk.payment_url}?{parse.urlencode(data)}"
        response = await requests_async.get(request_url)
        if response.status_code == 302:
            return str(response.next_request.url)

        return request_url

    async def create_payment(self, user_tg_id: int, product: DashasSpecial):
        order_id = int(str(datetime.now().timestamp()).replace(".", ""))
        async with DatabaseConnection.get_session() as session:
            session: AsyncSession
            result = await session.execute(
                select(User).filter(User.telegram_id == user_tg_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_tg_id} not found")
                raise ValueError(f"User {user_tg_id} not found")

            payment = Payment(
                user_id=user.id,
                order_id=str(order_id),
                amount=product.price,
                status=PaymentStatus.PENDING,
                payment_system=PaymentSystem.ROBOKASSA,
                created_at=datetime.now(),
                product=product.code,
            )
            session.add(payment)

        return await self._get_resolved_payment_link(
            user_tg_id,
            settings.rk.merchant_login,
            settings.rk.password_1,
            order_id,
            product,
            settings.rk.is_test
        )
