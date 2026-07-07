import s from "./Badge.module.css";

// Наличие товара. Цвет всегда продублирован текстом (не единственный сигнал).
export function Badge({ available }) {
  return (
    <span className={`${s.badge} ${available ? s.inStock : s.outStock}`}>
      {available ? "В наличии" : "Нет в наличии"}
    </span>
  );
}
