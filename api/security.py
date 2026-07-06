"""Валидация Telegram Mini App initData.

Telegram подписывает initData HMAC-SHA256 по секрету, производному от BOT_TOKEN.
Проверка обязательна: без неё клиент может подделать telegram_id.
См. https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl

from app.config import BOT_TOKEN


class InitDataError(ValueError):
    """initData отсутствует, повреждён, просрочен или подпись неверна."""


def validate_init_data(
    init_data: str,
    bot_token: str = BOT_TOKEN,
    max_age_seconds: Optional[int] = 86400,
) -> Dict[str, str]:
    """Проверяет подпись initData и возвращает распарсенные поля.

    Бросает InitDataError, если строка повреждена, подпись не сходится
    или (при заданном max_age_seconds) данные слишком старые.
    """
    if not init_data:
        raise InitDataError("empty initData")

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError as e:
        raise InitDataError("malformed initData") from e

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InitDataError("no hash in initData")

    # Data-check-string: оставшиеся поля key=value, отсортированные по ключу, через \n
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise InitDataError("bad initData signature")

    if max_age_seconds is not None:
        auth_date = parsed.get("auth_date")
        if auth_date is None:
            raise InitDataError("no auth_date in initData")
        try:
            issued_at = int(auth_date)
        except ValueError as e:
            raise InitDataError("invalid auth_date") from e
        if time.time() - issued_at > max_age_seconds:
            raise InitDataError("initData is too old")

    return parsed


def parse_user(fields: Dict[str, str]) -> Dict[str, Any]:
    """Достаёт и разбирает JSON-поле `user` из проверенных полей initData."""
    user_json = fields.get("user")
    if not user_json:
        raise InitDataError("no user in initData")
    try:
        return json.loads(user_json)
    except json.JSONDecodeError as e:
        raise InitDataError("malformed user in initData") from e
