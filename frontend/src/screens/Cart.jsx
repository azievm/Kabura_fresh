import { ShoppingCart } from "lucide-react";
import { CartRow } from "../components/CartRow.jsx";
import { Button } from "../components/Button.jsx";
import { formatPrice } from "../lib/format.js";
import s from "./Cart.module.css";

export function Cart({ cart, onInc, onDec, onRemove, onClear, onBrowse, busy }) {
  if (cart.items.length === 0) {
    return (
      <div className={s.empty}>
        <div className={s.emptyIcon}>
          <ShoppingCart size={40} strokeWidth={1.6} />
        </div>
        <p className={s.emptyTitle}>Корзина пуста</p>
        <p className={s.emptyText}>Загляните в каталог и добавьте свежие продукты.</p>
        <Button variant="primary" onClick={onBrowse}>
          Перейти в каталог
        </Button>
      </div>
    );
  }

  return (
    <div className={s.screen}>
      <ul className={s.list}>
        {cart.items.map((item) => (
          <CartRow
            key={item.id}
            item={item}
            disabled={busy}
            onInc={() => onInc(item)}
            onDec={() => onDec(item)}
            onRemove={() => onRemove(item)}
          />
        ))}
      </ul>

      <div className={s.summary}>
        <div className={s.totalRow}>
          <span>Итого</span>
          <span className={`${s.totalValue} tnum`}>{formatPrice(cart.total)}</span>
        </div>
        <Button variant="danger" full onClick={onClear} disabled={busy}>
          Очистить корзину
        </Button>
      </div>
    </div>
  );
}
