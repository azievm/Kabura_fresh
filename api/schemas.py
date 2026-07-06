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
    image_url: Optional[str] = None
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
    image_url: Optional[str] = None
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
