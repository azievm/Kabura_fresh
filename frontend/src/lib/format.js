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

export const CATEGORY_EMOJI = {
  fruits: "🍎",
  vegetables: "🥕",
  drinks: "🧃",
};
