"""Эндпоинты Mini App: профиль, каталог, корзина.

Логика повторяет поведение бота: каталог показывает розничную цену как
основную, а корзина считается по оптовой цене (как в add_to_cart/checkout).
"""
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import handlers as bot_handlers
from app.database import CartItem, Order, OrderItem, Product, User
from .deps import get_session, get_telegram_user, get_user_id
from .schemas import (
    CATEGORIES,
    DELIVERY_SLOTS,
    AddToCartIn,
    CartItemOut,
    CartOut,
    CategoryOut,
    CheckoutIn,
    CheckoutOut,
    ConfirmIn,
    ConfirmOut,
    DeliverySlotOut,
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


def _product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        description=p.description,
        category=p.category,
        retail_price=p.retail_price,
        wholesale_price=p.wholesale_price,
        amount=p.amount,
        has_image=bool(p.image_url),
        is_available=p.is_available,
    )


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
            select(Order)
            .where(Order.user_id == user_id, Order.status != "pending")
            .order_by(Order.created_at.desc())
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
    return [_product_out(p) for p in rows]


@router.get("/products/{product_id}", response_model=ProductOut)
async def product_detail(
    product_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProductOut:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return _product_out(product)


@router.get("/products/{product_id}/image")
async def product_image(
    product_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Отдаёт фото товара. image_url — это либо http(s)-ссылка (редирект),
    либо Telegram file_id (скачиваем через бота и отдаём байты).
    Без авторизации: <img> не может слать заголовок initData."""
    product = await session.get(Product, product_id)
    if product is None or not product.image_url:
        raise HTTPException(status_code=404, detail="no image")

    value = product.image_url
    if value.startswith("http://") or value.startswith("https://"):
        return RedirectResponse(value)

    bot = getattr(request.app.state, "bot", None)
    if bot is None:
        raise HTTPException(status_code=404, detail="no image")
    try:
        file = await bot.get_file(value)
        buf = await bot.download_file(file.file_path)
        data = buf.read()
    except Exception:
        logger.exception("Не удалось получить фото товара %s", product_id)
        raise HTTPException(status_code=404, detail="no image")

    return Response(
        content=data,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


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
                has_image=bool(product.image_url),
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


# --------------------------- оформление и оплата ---------------------------

@router.get("/delivery-slots", response_model=List[DeliverySlotOut])
async def delivery_slots() -> List[DeliverySlotOut]:
    return [DeliverySlotOut(**s) for s in DELIVERY_SLOTS]


@router.post("/checkout", response_model=CheckoutOut)
async def checkout(
    payload: CheckoutIn,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> CheckoutOut:
    """Создаёт платёж YooKassa и заказ со статусом 'pending' (снимок корзины).
    Заказ становится 'paid' после подтверждения оплаты — из webhook или /payment/confirm."""
    cart_items = (
        await session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
        )
    ).scalars().all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="cart is empty")

    total = sum(item.price * item.quantity for item in cart_items)

    if bot_handlers.payment_system is None:
        raise HTTPException(status_code=503, detail="payments are not configured")

    payment = await bot_handlers.payment_system.create_payment(
        amount=float(total),
        user_id=user_id,
        description=f"Kabura Fresh order {user_id}-{int(datetime.now().timestamp())}",
    )
    if not payment:
        raise HTTPException(status_code=502, detail="payment creation failed")

    order = Order(
        user_id=user_id,
        payment_id=payment["id"],
        status="pending",
        amount=total,
        customer_name=payload.name,
        customer_phone=payload.phone,
        delivery_address=payload.address,
        delivery_time=payload.delivery_time,
    )
    session.add(order)
    await session.flush()
    for item in cart_items:
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else f"Товар {item.product_id}",
                price=item.price,
                quantity=item.quantity,
            )
        )

    # Запоминаем контактные данные для префилла будущих заказов.
    user = await session.scalar(select(User).where(User.telegram_id == user_id))
    if user:
        user.customer_name = payload.name
        user.phone = payload.phone
        user.delivery_address = payload.address

    await session.commit()

    return CheckoutOut(
        payment_id=payment["id"],
        confirmation_url=payment["confirmation_url"],
        amount=float(payment["amount"]),
    )


async def _finalize_order(payment_id: str, session: AsyncSession, bot) -> "Order | None":
    """Подтверждает оплату у YooKassa и переводит pending-заказ в 'paid':
    очищает корзину и уведомляет админов. Идемпотентно, безопасно к повтору
    (webhook и ручная проверка вызывают одно и то же)."""
    order = await session.scalar(select(Order).where(Order.payment_id == payment_id))
    if order is None:
        return None
    if order.status in ("paid", "completed"):
        return order

    ps = bot_handlers.payment_system
    if ps is None or not await ps.verify_payment_success(payment_id):
        return order  # оплата ещё не подтверждена — заказ остаётся pending

    order.status = "paid"
    await session.execute(delete(CartItem).where(CartItem.user_id == order.user_id))
    items = (
        await session.scalars(select(OrderItem).where(OrderItem.order_id == order.id))
    ).all()
    await session.commit()

    if bot is not None:
        try:
            await bot_handlers.send_admin_notification(bot, order, items)
        except Exception:
            logger.exception("Не удалось уведомить админов о заказе %s", order.id)

    return order


@router.post("/payment/confirm", response_model=ConfirmOut)
async def confirm_payment(
    payload: ConfirmIn,
    request: Request,
    user_id: int = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> ConfirmOut:
    """Ручная проверка оплаты (fallback к webhook). Идемпотентна."""
    order = await session.scalar(select(Order).where(Order.payment_id == payload.payment_id))
    if order is None or order.user_id != user_id:
        raise HTTPException(status_code=404, detail="order not found")

    bot = getattr(request.app.state, "bot", None)
    order = await _finalize_order(payload.payment_id, session, bot)
    status = "ok" if order and order.status in ("paid", "completed") else "pending"
    return ConfirmOut(status=status, order_id=order.id if order else None)


@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> Dict[str, bool]:
    """Приём уведомлений YooKassa (payment.succeeded и т.п.).
    Статусу из тела НЕ доверяем — перепроверяем платёж через API в _finalize_order."""
    try:
        body = await request.json()
    except Exception:
        return {"ok": False}

    payment_id = ((body or {}).get("object") or {}).get("id")
    if not payment_id:
        return {"ok": True}

    bot = getattr(request.app.state, "bot", None)
    try:
        await _finalize_order(payment_id, session, bot)
    except Exception:
        logger.exception("Ошибка обработки webhook для платежа %s", payment_id)
    return {"ok": True}
