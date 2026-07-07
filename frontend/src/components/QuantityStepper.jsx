import { Minus, Plus } from "lucide-react";
import s from "./QuantityStepper.module.css";

// − N + для количества в корзине. Линейные иконки, без «пузырей».
export function QuantityStepper({ quantity, onDec, onInc, min = 1, disabled = false }) {
  return (
    <div className={s.stepper}>
      <button
        className={s.btn}
        onClick={onDec}
        disabled={disabled || quantity <= min}
        aria-label="Уменьшить количество"
      >
        <Minus size={16} strokeWidth={2.2} />
      </button>
      <span className={`${s.value} tnum`} aria-live="polite">
        {quantity}
      </span>
      <button
        className={s.btn}
        onClick={onInc}
        disabled={disabled}
        aria-label="Увеличить количество"
      >
        <Plus size={16} strokeWidth={2.2} />
      </button>
    </div>
  );
}
