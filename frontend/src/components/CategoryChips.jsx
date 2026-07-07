import { haptic } from "../lib/telegram.js";
import s from "./CategoryChips.module.css";

// Горизонтальный выбор категории. Активная — зелёная заливка.
export function CategoryChips({ categories, active, onChange }) {
  return (
    <div className={s.scroller}>
      <div className={s.row} role="tablist" aria-label="Категории">
        {categories.map((c) => (
          <button
            key={c.id}
            role="tab"
            aria-selected={c.id === active}
            className={`${s.chip} ${c.id === active ? s.active : ""}`}
            onClick={() => {
              haptic("light");
              onChange(c.id);
            }}
          >
            <span className={s.emoji} aria-hidden="true">
              {c.icon}
            </span>
            {c.label}
          </button>
        ))}
      </div>
    </div>
  );
}
