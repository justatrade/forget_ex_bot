import hashlib
import hmac
import httpx
import json
from collections.abc import MutableMapping
from datetime import datetime
from urllib.parse import urlencode

from shared.config import settings
from shared.config import setup_logger
from shared.database.connection import DatabaseConnection
from shared.database.models import Payment, User, PaymentStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


logger = setup_logger(__name__)


class ProdamusService:
    @staticmethod
    def _deep_int_to_string(dictionary: dict | MutableMapping):
        """Рекурсивно конвертирует все значения в строки"""
        for key, value in dictionary.items():
            if isinstance(value, MutableMapping):
                ProdamusService._deep_int_to_string(value)
            elif isinstance(value, (list, tuple)):
                for k, v in enumerate(value):
                    ProdamusService._deep_int_to_string({str(k): v})
            else:
                dictionary[key] = str(value)

    @staticmethod
    def _http_build_query(
        dictionary: dict | MutableMapping,
        parent_key: str = None,
    ) -> dict:
        """Преобразует вложенный словарь в формат query параметров"""
        items = []
        for key, value in dictionary.items():
            new_key = f"{parent_key}[{key}]" if parent_key else key
            if isinstance(value, MutableMapping):
                items.extend(ProdamusService._http_build_query(value, new_key).items())
            elif isinstance(value, (list, tuple)):
                for k, v in enumerate(value):
                    items.extend(
                        ProdamusService._http_build_query(
                            {str(k): v},
                            new_key
                        ).items()
                    )
            else:
                items.append((new_key, value))
        return dict(items)

    @staticmethod
    def _sign(data: dict, secret_key: str) -> str:
        """Генерирует HMAC SHA256 подпись"""
        ProdamusService._deep_int_to_string(data)

        data_json = json.dumps(
            data,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":")
        ).replace("/", "\\/")

        signature = hmac.new(
            secret_key.encode("utf8"),
            data_json.encode("utf8"),
            hashlib.sha256
        ).hexdigest()

        return signature

    @staticmethod
    async def create_payment(user_id: int, amount: int) -> str:
        """Создаёт платёж в Prodamus и возвращает URL для оплаты"""

        timestamp = int(datetime.now().timestamp())
        order_id = f"order_{timestamp}_{user_id}"

        async with DatabaseConnection.get_session() as session:
            session: AsyncSession
            result = await session.execute(
                select(User).filter(User.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {user_id} not found")
                raise ValueError(f"User {user_id} not found")

            payment = Payment(
                user_id=user.id,
                order_id=order_id,
                amount=amount,
                status=PaymentStatus.PENDING,
                created_at=datetime.now(),
            )
            session.add(payment)

        base_url = settings.prodamus.endpoint

        data = {
            "order_id": order_id,
            "customer_extra": str(user_id),
            "products": [
                {
                    "name": "Курс 'Забыть бывшего'",
                    "price": amount,
                    "quantity": 1,
                }
            ],
            "do": "link",
            "callbackType": "json",
            "sys": "maranaddasha",
            "urlSuccess": settings.app.success_url,
            "urlNotification": settings.app.webhook_url,
        }

        if settings.app.debug:
            data["sys"] = "test"
            data["demo_mode"] = "1"
            base_url = "https://demo.payform.ru"

        if user_id in settings.telegram.admin_id:
            discount_value = amount - 1
            data["discount_value"] = discount_value
            logger.debug(f"Admin discount applied: {data}")

        signature = ProdamusService._sign(
            data.copy(),
            settings.prodamus.get_secret(settings.app.debug)
        )
        data["signature"] = signature

        query_params = ProdamusService._http_build_query(data)
        long_url = f"{base_url}/?{urlencode(query_params)}"
        logger.debug(f"Full link {long_url}")
        payment_url = await ProdamusService._get_final_payment_url(
            long_url
        )

        logger.info(
            f"Payment link created for user {user_id}: {order_id}. "
            f"Link: {payment_url}"
        )
        return payment_url

    @staticmethod
    async def verify_webhook_signature(data: dict) -> bool:
        """Проверяет подпись webhook от Prodamus"""
        data_copy = data.copy()
        received_signature = data_copy.pop(
            settings.prodamus.var_prefix + "sign",
            data_copy.pop("sign", None),
        )

        calculated_signature = ProdamusService._sign(
            data_copy,
            settings.prodamus.get_secret(settings.app.debug),
        )
        is_valid = calculated_signature == received_signature

        if not is_valid:
            logger.warning(f"Invalid webhook signature for: {data}")

        return is_valid

    @staticmethod
    async def _get_final_payment_url(long_url: str) -> str:
        """Получает финальный URL из короткой ссылки Prodamus"""
        try:
            async with httpx.AsyncClient(follow_redirects=False, timeout=10.0) as client:
                response = await client.get(long_url)

                if response.status_code == 200:
                    final_url = response.text.strip()
                    logger.info(f"Final payment URL received: {final_url}")
                    return final_url
                elif response.status_code in (301, 302, 303, 307, 308):
                    logger.debug(
                        "text.strip() after redirected status code: "
                        f"{response.text.strip()}"
                    )
                    final_url = (
                        response.headers.get("Location", long_url)
                        if not response.text.strip()
                        else response.text.strip()
                    )
                    logger.info(f"Redirected to: {final_url}")
                    return final_url
                else:
                    logger.warning(
                        f"Unexpected response status {response.status_code},"
                        " using short URL"
                    )
                    return long_url

        except Exception as e:
            logger.error(
                f"Failed to get final URL: {e}, using short URL as fallback"
            )
            return long_url
