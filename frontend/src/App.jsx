import { useEffect, useState, useCallback } from "react";
import { Header } from "./components/Header.jsx";
import { Catalog } from "./screens/Catalog.jsx";
import { Cart } from "./screens/Cart.jsx";
import { api } from "./lib/api.js";
import { tg, haptic } from "./lib/telegram.js";
import { formatPrice } from "./lib/format.js";

const GREEN = "#2E7D46";

export function App() {
  const [screen, setScreen] = useState("catalog"); // 'catalog' | 'cart'
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [cart, setCart] = useState({ items: [], total: 0, count: 0 });
  const [cartBusy, setCartBusy] = useState(false);

  // Категории + корзина при старте
  useEffect(() => {
    api
      .categories()
      .then((cats) => {
        setCategories(cats);
        setActiveCategory((prev) => prev ?? cats[0]?.id ?? null);
      })
      .catch(() => setError(true));
    api.getCart().then(setCart).catch(() => {});
  }, []);

  // Товары активной категории
  useEffect(() => {
    if (!activeCategory) return;
    let cancelled = false;
    setLoading(true);
    setError(false);
    api
      .products(activeCategory)
      .then((items) => !cancelled && setProducts(items))
      .catch(() => !cancelled && setError(true))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [activeCategory]);

  // --- операции с корзиной ---
  const runCart = useCallback(async (fn) => {
    setCartBusy(true);
    try {
      setCart(await fn());
    } catch {
      /* оставляем прежнее состояние */
    } finally {
      setCartBusy(false);
    }
  }, []);

  const handleAdd = useCallback(
    (product) => {
      haptic("light");
      return runCart(() => api.addToCart(product.id, 1));
    },
    [runCart]
  );
  const handleInc = useCallback((item) => runCart(() => api.updateCartItem(item.id, item.quantity + 1)), [runCart]);
  const handleDec = useCallback((item) => runCart(() => api.updateCartItem(item.id, item.quantity - 1)), [runCart]);
  const handleRemove = useCallback((item) => {
    haptic("light");
    return runCart(() => api.removeCartItem(item.id));
  }, [runCart]);
  const handleClear = useCallback(() => {
    haptic("medium");
    return runCart(() => api.clearCart());
  }, [runCart]);

  // --- Telegram BackButton: показываем на экране корзины ---
  useEffect(() => {
    const bb = tg?.BackButton;
    if (!bb) return;
    if (screen === "cart") {
      const go = () => setScreen("catalog");
      bb.show();
      bb.onClick(go);
      return () => {
        bb.offClick(go);
        bb.hide();
      };
    }
    bb.hide();
  }, [screen]);

  // --- Telegram MainButton: контекстный, зелёный ---
  useEffect(() => {
    const mb = tg?.MainButton;
    if (!mb) return;

    if (cart.count === 0) {
      mb.hide();
      return;
    }

    if (screen === "catalog") {
      mb.setParams({
        text: `Корзина · ${cart.count} · ${formatPrice(cart.total)}`,
        color: GREEN,
        text_color: "#FFFFFF",
        is_visible: true,
      });
      const go = () => setScreen("cart");
      mb.onClick(go);
      return () => mb.offClick(go);
    }

    // screen === 'cart'
    mb.setParams({
      text: `Оформить заказ · ${formatPrice(cart.total)}`,
      color: GREEN,
      text_color: "#FFFFFF",
      is_visible: true,
    });
    const checkout = () =>
      tg?.showAlert
        ? tg.showAlert("Оформление заказа скоро будет доступно.")
        : undefined;
    mb.onClick(checkout);
    return () => mb.offClick(checkout);
  }, [screen, cart.count, cart.total]);

  const cartIds = new Set(cart.items.map((i) => i.product_id));

  return (
    <>
      <Header cartCount={cart.count} onCart={() => setScreen("cart")} />
      {screen === "catalog" ? (
        <Catalog
          categories={categories}
          activeCategory={activeCategory}
          onCategoryChange={setActiveCategory}
          products={products}
          loading={loading}
          error={error}
          cartIds={cartIds}
          onAdd={handleAdd}
        />
      ) : (
        <Cart
          cart={cart}
          busy={cartBusy}
          onInc={handleInc}
          onDec={handleDec}
          onRemove={handleRemove}
          onClear={handleClear}
          onBrowse={() => setScreen("catalog")}
        />
      )}
    </>
  );
}
