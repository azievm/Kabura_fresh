import { formatPrice, unitsForCategory } from "../lib/format.js";
import s from "./PriceTag.module.css";

// Розничная цена — крупно оранжевым (герой), опт — тихой второй строкой.
// Единицы берём по категории (надёжное правило магазина), не из поля amount.
export function PriceTag({ retail, wholesale, category }) {
  const units = unitsForCategory(category);
  return (
    <div className={s.wrap}>
      <div className={s.retail}>
        <span className="tnum">{formatPrice(retail)}</span>
        <span className={s.unit}>/{units.retail}</span>
      </div>
      {wholesale != null && (
        <div className={s.wholesale}>
          опт <span className="tnum">{formatPrice(wholesale)}</span>/{units.wholesale}
        </div>
      )}
    </div>
  );
}
