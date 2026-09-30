"""Единые правила цен: корзина в боте и в Mini App считается одинаково."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

_CENT = Decimal("0.01")


def unit_price(product) -> float:
    """Цена единицы в корзине — оптовая; если опт не задан, откат на розничную."""
    if product.wholesale_price is not None:
        return product.wholesale_price
    return product.retail_price


def money(value) -> float:
    """Округление денежной суммы до копеек (без накопления ошибок float)."""
    return float(Decimal(str(value)).quantize(_CENT, rounding=ROUND_HALF_UP))


def line_total(price, quantity) -> float:
    return money(Decimal(str(price)) * quantity)


def cart_total(items: Iterable) -> float:
    """Сумма позиций (объекты с полями price и quantity)."""
    return money(sum((Decimal(str(i.price)) * i.quantity for i in items), Decimal("0")))
