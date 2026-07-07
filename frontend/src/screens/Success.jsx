import { CheckCircle2 } from "lucide-react";
import { Button } from "../components/Button.jsx";
import s from "./Success.module.css";

export function Success({ orderId, onBrowse, onOrders }) {
  return (
    <div className={s.wrap}>
      <div className={s.icon}>
        <CheckCircle2 size={44} strokeWidth={1.6} />
      </div>
      <h2 className={s.title}>Заказ оформлен!</h2>
      <p className={s.text}>
        {orderId ? `Заказ №${orderId} принят. ` : ""}
        Мы свяжемся с вами для подтверждения и привезём всё свежим.
      </p>
      <div className={s.actions}>
        <Button variant="primary" full onClick={onBrowse}>
          Вернуться в каталог
        </Button>
        <Button variant="secondary" full onClick={onOrders}>
          Мои заказы
        </Button>
      </div>
    </div>
  );
}
