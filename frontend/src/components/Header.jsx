import { ShoppingCart } from "lucide-react";
import s from "./Header.module.css";

export function Header({ cartCount = 0, onCart }) {
  return (
    <header className={s.header}>
      <div className={s.wordmark}>
        Kabura<span className={s.fresh}>Fresh</span>
      </div>
      <button className={s.cart} onClick={onCart} aria-label="Корзина">
        <ShoppingCart size={22} strokeWidth={2} />
        {cartCount > 0 && <span className={s.count}>{cartCount}</span>}
      </button>
    </header>
  );
}
