import { formatDate, formatPrice, orderStatus } from "../lib/format.js";
import s from "./OrderCard.module.css";

export function OrderCard({ order }) {
  const status = orderStatus(order.status);
  return (
    <article className={s.card}>
      <div className={s.head}>
        <span className={s.num}>Заказ №{order.id}</span>
        <span className={`${s.status} ${status.tone === "ok" ? s.ok : s.muted}`}>
          {status.label}
        </span>
      </div>
      {order.created_at && <div className={s.date}>{formatDate(order.created_at)}</div>}

      <ul className={s.items}>
        {order.items.map((it, i) => (
          <li key={i} className={s.item}>
            <span className={s.itemName}>
              {it.product_name} <span className={s.mult}>× {it.quantity}</span>
            </span>
            <span className="tnum">{formatPrice(it.price * it.quantity)}</span>
          </li>
        ))}
      </ul>

      <div className={s.total}>
        <span>Итого</span>
        <span className={`${s.totalValue} tnum`}>{formatPrice(order.amount)}</span>
      </div>

      {order.delivery_address && (
        <div className={s.addr}>Доставка: {order.delivery_address}</div>
      )}
    </article>
  );
}
