import asyncio
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional

from yookassa import Configuration, Payment, Refund

from .config import PAYMENT_RECEIPT_EMAIL, PAYMENT_VAT_CODE
from .pricing import money

PaymentStatus = Literal["pending", "waiting_for_capture", "succeeded", "canceled"]

logger = logging.getLogger(__name__)


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Телефон в формате YooKassa (79991234567) или None, если не распознан."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits[0] in "78":
        return "7" + digits[1:]
    if len(digits) == 10:
        return "7" + digits
    return None


class PaymentSystem:
    def __init__(self, shop_id: str, secret_key: str):
        """Initialize payment system with credentials"""
        if not shop_id or not secret_key:
            raise RuntimeError("Payment credentials are not configured")

        if not (secret_key.startswith("test_") or secret_key.startswith("live_")):
            raise RuntimeError(
                "YooKassa secret key has wrong format. Use the Secret key from Merchant Profile, "
                "it should start with test_ or live_."
            )

        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key

    @staticmethod
    def _build_receipt(
        items: List[Dict], amount: float, user_id: int, phone: Optional[str], description: str
    ) -> Dict:
        """Чек 54-ФЗ: реальные товарные позиции и контакт покупателя.
        Если позиции не переданы — одна позиция на всю сумму."""
        normalized = _normalize_phone(phone)
        customer = {"phone": normalized} if normalized else {"email": PAYMENT_RECEIPT_EMAIL.format(user_id=user_id)}

        receipt_items = [
            {
                "description": item["name"][:128],
                "quantity": str(item["quantity"]),
                "amount": {"value": f"{money(item['price']):.2f}", "currency": "RUB"},
                "vat_code": PAYMENT_VAT_CODE,
                "payment_subject": "commodity",
                "payment_mode": "full_payment",
            }
            for item in items
        ]
        if not receipt_items:
            receipt_items = [{
                "description": description[:128],
                "quantity": "1.00",
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "vat_code": PAYMENT_VAT_CODE,
                "payment_subject": "commodity",
                "payment_mode": "full_payment",
            }]
        return {"customer": customer, "items": receipt_items}

    async def create_payment(
        self,
        amount: float,
        user_id: int,
        description: str = "Order payment",
        return_url: str = "https://t.me/kaburaf_bot",
        items: Optional[List[Dict]] = None,
        phone: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """Создаёт платёж с чеком. items: [{name, price, quantity}] — состав корзины."""
        try:
            amount = money(amount)
            payment_data = {
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "confirmation": {"type": "redirect", "return_url": return_url},
                "capture": True,
                "description": description[:128],
                "metadata": {
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                },
                "receipt": self._build_receipt(items or [], amount, user_id, phone, description),
            }

            # SDK YooKassa синхронный — выносим в поток, чтобы не блокировать event loop
            payment = await asyncio.to_thread(Payment.create, payment_data, str(uuid.uuid4()))

            return {
                "id": payment.id,
                "status": payment.status,
                "confirmation_url": payment.confirmation.confirmation_url,
                "amount": float(payment.amount.value),
            }
        except Exception:
            logger.exception("PaymentSystem.create_payment error")
            return None

    async def check_payment_status(self, payment_id: str) -> Optional[PaymentStatus]:
        try:
            payment = await asyncio.to_thread(Payment.find_one, payment_id)
            return payment.status
        except Exception:
            logger.exception("Не удалось проверить статус платежа %s", payment_id)
            return None

    async def verify_payment_success(self, payment_id: str) -> bool:
        return await self.check_payment_status(payment_id) == "succeeded"

    async def refund_payment(self, payment_id: str) -> bool:
        try:
            payment = await asyncio.to_thread(Payment.find_one, payment_id)
            if payment.status != "succeeded":
                return False
            refund = await asyncio.to_thread(
                Refund.create,
                {"payment_id": payment_id, "amount": payment.amount},
                str(uuid.uuid4()),
            )
            return refund.status == "succeeded"
        except Exception:
            logger.exception("Ошибка при возврате платежа %s", payment_id)
            return False
