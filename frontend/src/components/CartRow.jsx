import { Trash2 } from "lucide-react";
import { ProductThumb } from "./ProductThumb.jsx";
import { QuantityStepper } from "./QuantityStepper.jsx";
import { formatPrice } from "../lib/format.js";
import s from "./CartRow.module.css";

// Строка корзины: фото, название, цена за единицу, степпер, итог строки, удаление.
export function CartRow({ item, onInc, onDec, onRemove, disabled = false }) {
  return (
    <li className={s.row}>
      <ProductThumb image={item.image_url} name={item.name} available={item.is_available} />
      <div className={s.info}>
        <div className={s.name}>{item.name}</div>
        <div className={s.unit}>
          <span className="tnum">{formatPrice(item.price)}</span> за ед.
        </div>
        <QuantityStepper
          quantity={item.quantity}
          onInc={onInc}
          onDec={onDec}
          disabled={disabled}
        />
      </div>
      <div className={s.right}>
        <div className={`${s.total} tnum`}>{formatPrice(item.line_total)}</div>
        <button
          className={s.remove}
          onClick={onRemove}
          disabled={disabled}
          aria-label={`Удалить ${item.name} из корзины`}
        >
          <Trash2 size={18} strokeWidth={1.9} />
        </button>
      </div>
    </li>
  );
}
