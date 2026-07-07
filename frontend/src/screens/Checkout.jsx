import { useEffect, useState } from "react";
import { CreditCard, RefreshCw } from "lucide-react";
import { Button } from "../components/Button.jsx";
import { api } from "../lib/api.js";
import { tg, haptic } from "../lib/telegram.js";
import { formatPrice } from "../lib/format.js";
import s from "./Checkout.module.css";

export function Checkout({ cartTotal, defaults, onSuccess }) {
  const [name, setName] = useState(defaults?.customer_name || "");
  const [phone, setPhone] = useState(defaults?.phone || "");
  const [address, setAddress] = useState(defaults?.delivery_address || "");
  const [slots, setSlots] = useState([]);
  const [slot, setSlot] = useState("");
  const [phase, setPhase] = useState("form"); // 'form' | 'paying'
  const [payment, setPayment] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.deliverySlots().then(setSlots).catch(() => {});
  }, []);

  const valid = name.trim() && phone.trim().length >= 5 && address.trim() && slot;

  async function handlePay() {
    if (!valid || busy) return;
    setBusy(true);
    setError("");
    haptic("medium");
    try {
      const data = { name: name.trim(), phone: phone.trim(), address: address.trim(), delivery_time: slot };
      const res = await api.checkout(data);
      setPayment({ ...res, form: data });
      setPhase("paying");
      if (tg?.openLink) tg.openLink(res.confirmation_url);
      else window.open(res.confirmation_url, "_blank");
    } catch (e) {
      setError("Не удалось создать платёж. Попробуйте ещё раз.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCheck() {
    if (busy || !payment) return;
    setBusy(true);
    setError("");
    try {
      const res = await api.confirmPayment({ ...payment.form, payment_id: payment.payment_id });
      if (res.status === "ok") {
        haptic("medium");
        onSuccess(res.order_id);
      } else {
        setError("Оплата ещё не поступила. Завершите оплату и нажмите проверить.");
      }
    } catch (e) {
      setError("Не удалось проверить оплату. Попробуйте ещё раз.");
    } finally {
      setBusy(false);
    }
  }

  if (phase === "paying") {
    return (
      <div className={s.screen}>
        <div className={s.payCard}>
          <div className={s.payIcon}>
            <CreditCard size={30} strokeWidth={1.7} />
          </div>
          <h2 className={s.payTitle}>Ожидаем оплату</h2>
          <p className={s.payText}>
            Мы открыли страницу оплаты на {formatPrice(payment.amount)}. После оплаты
            вернитесь сюда и нажмите «Проверить оплату».
          </p>
          {error && <p className={s.error}>{error}</p>}
          <Button variant="primary" full onClick={handleCheck} disabled={busy}>
            <RefreshCw size={18} /> Проверить оплату
          </Button>
          <button
            className={s.link}
            onClick={() => tg?.openLink?.(payment.confirmation_url)}
          >
            Открыть страницу оплаты ещё раз
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={s.screen}>
      <div className={s.field}>
        <label className={s.label} htmlFor="co-name">Имя</label>
        <input
          id="co-name"
          className={s.input}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Как к вам обращаться"
          autoComplete="name"
        />
      </div>

      <div className={s.field}>
        <label className={s.label} htmlFor="co-phone">Телефон</label>
        <input
          id="co-phone"
          className={s.input}
          type="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          placeholder="+7 ..."
          autoComplete="tel"
        />
      </div>

      <div className={s.field}>
        <label className={s.label} htmlFor="co-addr">Адрес доставки</label>
        <textarea
          id="co-addr"
          className={`${s.input} ${s.textarea}`}
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Улица, дом, квартира"
          rows={2}
        />
      </div>

      <div className={s.field}>
        <span className={s.label}>Время доставки</span>
        <div className={s.slots}>
          {slots.map((sl) => (
            <button
              key={sl.id}
              type="button"
              className={`${s.slot} ${slot === sl.id ? s.slotActive : ""}`}
              onClick={() => setSlot(sl.id)}
            >
              {sl.label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className={s.error}>{error}</p>}

      <div className={s.bar}>
        <Button variant="primary" full onClick={handlePay} disabled={!valid || busy}>
          <CreditCard size={18} /> Оплатить · {formatPrice(cartTotal)}
        </Button>
      </div>
    </div>
  );
}
