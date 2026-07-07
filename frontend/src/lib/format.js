// Формат денег и единиц измерения (единый для всего фронта).

export function formatPrice(n) {
  if (n == null) return "";
  const rounded = Number.isInteger(n) ? n : Math.round(n * 100) / 100;
  return rounded.toLocaleString("ru-RU") + " ₽"; // тонкий пробел + ₽
}

// Единицы измерения по категории — правило магазина (раздел «О сервисе»):
// фрукты/овощи продаются в розницу за кг и оптом за ящик, напитки — за шт и упаковку.
// Берём отсюда, а не из поля amount: оно в данных заполнено неоднородно.
export function unitsForCategory(category) {
  if (category === "drinks") return { retail: "шт", wholesale: "упак" };
  return { retail: "кг", wholesale: "ящик" };
}

// Дата заказа: ISO -> «7 июля 2026».
export function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}

// Человекочитаемые статусы заказа. tone: 'ok' | 'muted' — для цвета плашки.
export const ORDER_STATUS = {
  new: { label: "Новый", tone: "muted" },
  paid: { label: "Оплачен", tone: "ok" },
  completed: { label: "Выполнен", tone: "ok" },
  cancelled: { label: "Отменён", tone: "muted" },
};

export function orderStatus(status) {
  return ORDER_STATUS[status] || { label: status, tone: "muted" };
}

export const CATEGORY_EMOJI = {
  fruits: "🍎",
  vegetables: "🥕",
  drinks: "🧃",
};
