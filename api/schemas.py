"""Pydantic-схемы ответов и запросов Mini App API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# Категории каталога — те же, что в боте (get_catalog_keyboard) и дизайн-системе
CATEGORIES = [
    {"id": "fruits", "label": "Фрукты", "icon": "🍎"},
    {"id": "vegetables", "label": "Овощи", "icon": "🥕"},
    {"id": "drinks", "label": "Напитки", "icon": "🧃"},
]


class CategoryOut(BaseModel):
    id: str
    label: str
    icon: str


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str
    retail_price: float
    wholesale_price: Optional[float] = None
    amount: Optional[str] = None  # единица измерения / фасовка ("кг", "5,5 кг", "шт")
    has_image: bool = False       # фото грузится через /api/products/{id}/image
    is_available: bool = True


class MeResponse(BaseModel):
    telegram_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    delivery_address: Optional[str] = None


class CartItemOut(BaseModel):
    id: int
    product_id: int
    name: str
    price: float           # цена за единицу (как её оплатит клиент — опт, как в боте)
    quantity: int
    line_total: float
    amount: Optional[str] = None
    has_image: bool = False
    is_available: bool = True


class CartOut(BaseModel):
    items: List[CartItemOut]
    total: float
    count: int             # суммарное количество единиц


class AddToCartIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class UpdateCartItemIn(BaseModel):
    quantity: int = Field(ge=1)


class OrderItemOut(BaseModel):
    product_name: str
    price: float
    quantity: int


class OrderOut(BaseModel):
    id: int
    amount: float
    status: str
    created_at: Optional[datetime] = None
    delivery_address: Optional[str] = None
    delivery_time: Optional[str] = None
    items: List[OrderItemOut]


class ProfileOut(BaseModel):
    telegram_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    delivery_address: Optional[str] = None
    orders: List[OrderOut]


# Интервалы доставки — те же, что в боте (delivery_morning/day/evening)
DELIVERY_SLOTS = [
    {"id": "morning", "label": "Утро (9–12)"},
    {"id": "day", "label": "День (12–18)"},
    {"id": "evening", "label": "Вечер (18–22)"},
]


class DeliverySlotOut(BaseModel):
    id: str
    label: str


class CheckoutIn(BaseModel):
    name: str = Field(min_length=1)
    phone: str = Field(min_length=5)
    address: str = Field(min_length=1)
    delivery_time: str


class CheckoutOut(BaseModel):
    payment_id: str
    confirmation_url: str
    amount: float


class ConfirmIn(BaseModel):
    payment_id: str


class ConfirmOut(BaseModel):
    status: str  # 'ok' — оплата подтверждена, 'pending' — оплата ещё не прошла
    order_id: Optional[int] = None
