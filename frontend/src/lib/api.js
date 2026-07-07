// HTTP-клиент к FastAPI. Фронт и API — один origin, поэтому пути относительные.
// Авторизация — через подписанный Telegram initData в заголовке.
import { initData } from "./telegram.js";

async function req(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: "tma " + initData,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.json())?.detail ?? "";
    } catch {
      /* ignore */
    }
    throw new Error(`${res.status}${detail ? `: ${detail}` : ""}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  me: () => req("/api/me"),
  categories: () => req("/api/categories"),
  products: (category) =>
    req(`/api/products${category ? `?category=${encodeURIComponent(category)}` : ""}`),
  product: (id) => req(`/api/products/${id}`),
  getCart: () => req("/api/cart"),
  addToCart: (productId, quantity = 1) =>
    req("/api/cart", { method: "POST", body: JSON.stringify({ product_id: productId, quantity }) }),
  updateCartItem: (itemId, quantity) =>
    req(`/api/cart/${itemId}`, { method: "PATCH", body: JSON.stringify({ quantity }) }),
  removeCartItem: (itemId) => req(`/api/cart/${itemId}`, { method: "DELETE" }),
  clearCart: () => req("/api/cart", { method: "DELETE" }),
  profile: () => req("/api/profile"),
  deliverySlots: () => req("/api/delivery-slots"),
  checkout: (data) => req("/api/checkout", { method: "POST", body: JSON.stringify(data) }),
  confirmPayment: (paymentId) =>
    req("/api/payment/confirm", { method: "POST", body: JSON.stringify({ payment_id: paymentId }) }),
};
