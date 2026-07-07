import { Phone, MapPin, Package } from "lucide-react";
import { OrderCard } from "../components/OrderCard.jsx";
import s from "./Profile.module.css";

function displayName(p) {
  return (
    p.customer_name ||
    [p.first_name, p.last_name].filter(Boolean).join(" ") ||
    "Профиль"
  );
}

export function Profile({ profile, loading, error }) {
  if (loading) {
    return (
      <div className={s.screen}>
        <div className={s.skeletonCard} />
        <div className={s.skeletonCard} style={{ height: 120 }} />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className={s.state}>
        <p>Не удалось загрузить профиль.</p>
        <p className={s.muted}>Попробуйте открыть ещё раз.</p>
      </div>
    );
  }

  const orders = profile.orders || [];

  return (
    <div className={s.screen}>
      <section className={s.user}>
        <div className={s.name}>{displayName(profile)}</div>
        {profile.username && <div className={s.username}>@{profile.username}</div>}
        <dl className={s.fields}>
          <div className={s.field}>
            <Phone size={16} className={s.icon} />
            <span>{profile.phone || "Телефон не указан"}</span>
          </div>
          <div className={s.field}>
            <MapPin size={16} className={s.icon} />
            <span>{profile.delivery_address || "Адрес не указан"}</span>
          </div>
        </dl>
      </section>

      <h2 className={s.heading}>История заказов</h2>

      {orders.length === 0 ? (
        <div className={s.emptyOrders}>
          <Package size={32} strokeWidth={1.6} className={s.emptyIcon} />
          <p>Заказов пока нет</p>
        </div>
      ) : (
        <div className={s.orders}>
          {orders.map((o) => (
            <OrderCard key={o.id} order={o} />
          ))}
        </div>
      )}
    </div>
  );
}
