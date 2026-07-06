"""Эндпоинты Mini App: профиль, каталог, корзина.

Логика повторяет поведение бота: каталог показывает розничную цену как
основную, а корзина считается по оптовой цене (как в add_to_cart/checkout).
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import CartItem, Order, OrderItem, Product, User
from .deps import get_session, get_telegram_user, get_user_id
from .schemas import (
    CATEGORIES,
    AddToCartIn,
    CartItemOut,
    CartOut,
    CategoryOut,
    MeResponse,
    OrderItemOut,
    OrderOut,
    ProductOut,
    ProfileOut,
    UpdateCartItemIn,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


def _cart_price(product: Product) -> float:
    """Цена единицы в корзине — оптовая (как в боте), с откатом на розничную,
    если опт не задан (иначе расчёт суммы упал бы на None)."""
    if product.wholesale_price is not None:
        return product.wholesale_price
    return product.retail_price


async def _get_or_create_user(tg_user: Dict[str, Any], session: AsyncSession) -> User:
    """Возвращает запись пользователя, создавая её при первом заходе.
    Пользователь уже проверен по подписи initData, так что доверяем данным."""
    telegram_id = int(tg_user["id"])
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            last_name=tg_user.get("last_name"),
        )
        session.add(user)
        await session.commit()
        logger.info("Mini App: создан новый пользователь telegram_id=%s", telegram_id)
    return user


# --------------------------- профиль ---------------------------

@router.get("/me", response_model=MeResponse)
async def me(
    tg_user: Dict[str, Any] = Depends(get_telegram_user),
    session: AsyncSession = Depends(get_session),
) -> MeResponse:
    """Профиль текущего пользователя; создаёт запись при первом заходе."""
    user = await _get_or_create_user(tg_user, session)
    return MeResponse(
        telegram_id=user.telegram_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        customer_name=user.customer_name,
        phone=user.phone,
        delivery_address=user.delivery_address,
    )


@router.get("/profile", response_model=ProfileOut)
async def profile(
    tg_user: Dict[str, Any] = Depends(get_telegram_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileOut:
    """Профиль пользователя + история его заказов с составом."""
    user = await _get_or_create_user(tg_user, session)
    user_id = user.telegram_id

    orders = (
        await session.scalars(
            select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
    ).all()

    order_out: List[OrderOut] = []
    for order in orders:
        items = (
            await session.scalars(
                select(OrderItem).where(OrderItem.order_id == order.id)
            )
        ).all()
        order_out.append(
            OrderOut(
                id=order.id,
                amount=float(order.amount),
                status=order.status,
                created_at=order.created_at,
                delivery_address=order.delivery_address,
                delivery_time=order.delivery_time,
                items=[
                    OrderItemOut(product_name=i.product_name, price=i.price, quantity=i.quantity)
                    for i in items
                ],
            )
        )

    return ProfileOut(
        telegram_id=user.telegram_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        customer_name=user.customer_name,
        phone=user.phone,
        delivery_address=user.delivery_address,
        orders=order_out,
    )


# --------------------------- каталог ---------------------------

@router.get("/categories", response_model=List[CategoryOut])
async def categories() -> List[CategoryOut]:
    return [CategoryOut(**c) for c in CATEGORIES]


@router.get("/products", response_model=List[ProductOut])
async def products(
    category: str | None = None,
    available_only: bool = False,
    session: AsyncSession = Depends(get_session),
) -> List[ProductOut]:
    query = select(Product)
    if category:
        query = query.where(Product.category == category)
    if available_only:
        query = query.where(Product.is_available == True)  # noqa: E712
    query = query.order_by(Product.name)

    rows = (await session.scalars(query)).all()
    return [ProductOut.model_validate(p, from_attributes=True) for p in rows]


@router.get("/products/{product_id}", response_model=ProductOut)
async def product_detail(
    product_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProductOut:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return ProductOut.model_validate(product, from_attributes=True)


# --------------------------- корзина ---------------------------

async def _build_cart(user_id: int, session: AsyncSession) -> CartOut:
    rows = (
        await session.execute(
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.id)
        )
    ).all()

    items: List[CartItemOut] = []
    total = 0.0
    count = 0
    for cart_item, product in rows:
        line_total = cart_item.price * cart_item.quantity
        total += line_total
        count += cart_item.quantity
        items.append(
            CartItemOut(
                id=cart_item.id,
                product_id=cart_item.product_id,
                name=product.name,
                price=cart_item.price,
                quantity=cart_item.quantity,
                line_total=line_total,
                amount=product.amount,
                image_url=product.image_url,
                is_available=product.is_available,
            )
        )

    return CartOut(items=items, total=total, count=count)


@router.get("/cart", response_model=CartOut)
async def get_cart(
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    return await _build_cart(user_id, session)


@router.post("/cart", response_model=CartOut)
async def add_to_cart(
    payload: AddToCartIn,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    product = await session.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")

    existing = await session.scalar(
        select(CartItem).where(
            (CartItem.user_id == user_id) & (CartItem.product_id == payload.product_id)
        )
    )
    if existing:
        existing.quantity += payload.quantity
    else:
        session.add(
            CartItem(
                user_id=user_id,
                product_id=product.id,
                product_name=product.name,
                price=_cart_price(product),
                quantity=payload.quantity,
            )
        )
    await session.commit()
    return await _build_cart(user_id, session)


@router.patch("/cart/{item_id}", response_model=CartOut)
async def update_cart_item(
    item_id: int,
    payload: UpdateCartItemIn,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    item = await session.get(CartItem, item_id)
    if item is None or item.user_id != user_id:
        raise HTTPException(status_code=404, detail="cart item not found")
    item.quantity = payload.quantity
    await session.commit()
    return await _build_cart(user_id, session)


@router.delete("/cart/{item_id}", response_model=CartOut)
async def remove_cart_item(
    item_id: int,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    item = await session.get(CartItem, item_id)
    if item is None or item.user_id != user_id:
        raise HTTPException(status_code=404, detail="cart item not found")
    await session.delete(item)
    await session.commit()
    return await _build_cart(user_id, session)


@router.delete("/cart", response_model=CartOut)
async def clear_cart(
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> CartOut:
    await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
    await session.commit()
    return await _build_cart(user_id, session)
