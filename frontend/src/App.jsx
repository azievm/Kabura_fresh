import { useEffect, useState, useCallback } from "react";
import { Header } from "./components/Header.jsx";
import { Catalog } from "./screens/Catalog.jsx";
import { Cart } from "./screens/Cart.jsx";
import { Profile } from "./screens/Profile.jsx";
import { Checkout } from "./screens/Checkout.jsx";
import { Success } from "./screens/Success.jsx";
import { api } from "./lib/api.js";
import { tg, haptic } from "./lib/telegram.js";
import { formatPrice } from "./lib/format.js";

const GREEN = "#2E7D46";

export function App() {
  const [screen, setScreen] = useState("catalog"); // 'catalog' | 'cart' | 'profile'
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [cart, setCart] = useState({ items: [], total: 0, count: 0 });
  const [cartBusy, setCartBusy] = useState(false);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState(false);
  const [me, setMe] = useState(null); // для префилла формы оформления
  const [lastOrderId, setLastOrderId] = useState(null);

  // Категории + корзина + профиль при старте
  useEffect(() => {
    api
      .categories()
      .then((cats) => {
        setCategories(cats);
        setActiveCategory((prev) => prev ?? cats[0]?.id ?? null);
      })
      .catch(() => setError(true));
    api.getCart().then(setCart).catch(() => {});
    api.me().then(setMe).catch(() => {});
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

  // Профиль подгружаем при входе на экран (свежая история заказов)
  useEffect(() => {
    if (screen !== "profile") return;
    let cancelled = false;
    setProfileLoading(true);
    setProfileError(false);
    api
      .profile()
      .then((data) => !cancelled && setProfile(data))
      .catch(() => !cancelled && setProfileError(true))
      .finally(() => !cancelled && setProfileLoading(false));
    return () => {
      cancelled = true;
    };
  }, [screen]);

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

  // --- Telegram BackButton: на любом экране кроме каталога ---
  useEffect(() => {
    const bb = tg?.BackButton;
    if (!bb) return;
    if (screen !== "catalog") {
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

  // --- Telegram MainButton: контекстный, зелёный (каталог и корзина) ---
  useEffect(() => {
    const mb = tg?.MainButton;
    if (!mb) return;

    if (screen === "catalog" && cart.count > 0) {
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

    if (screen === "cart" && cart.count > 0) {
      mb.setParams({
        text: `Оформить заказ · ${formatPrice(cart.total)}`,
        color: GREEN,
        text_color: "#FFFFFF",
        is_visible: true,
      });
      const go = () => setScreen("checkout");
      mb.onClick(go);
      return () => mb.offClick(go);
    }

    // на checkout/profile/success собственную кнопку рисуют экраны или её нет
    mb.hide();
  }, [screen, cart.count, cart.total]);

  const handleOrderSuccess = useCallback((orderId) => {
    setLastOrderId(orderId);
    setCart({ items: [], total: 0, count: 0 }); // корзина очищена на сервере
    setScreen("success");
  }, []);

  const cartIds = new Set(cart.items.map((i) => i.product_id));

  return (
    <>
      <Header
        cartCount={cart.count}
        onCart={() => setScreen("cart")}
        onProfile={() => setScreen("profile")}
      />
      {screen === "catalog" && (
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
      )}
      {screen === "cart" && (
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
      {screen === "profile" && (
        <Profile profile={profile} loading={profileLoading} error={profileError} />
      )}
      {screen === "checkout" && (
        <Checkout cartTotal={cart.total} defaults={me} onSuccess={handleOrderSuccess} />
      )}
      {screen === "success" && (
        <Success
          orderId={lastOrderId}
          onBrowse={() => setScreen("catalog")}
          onOrders={() => setScreen("profile")}
        />
      )}
    </>
  );
}
