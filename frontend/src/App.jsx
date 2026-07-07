import { useEffect, useState, useCallback } from "react";
import { Header } from "./components/Header.jsx";
import { Catalog } from "./screens/Catalog.jsx";
import { api } from "./lib/api.js";

export function App() {
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [cart, setCart] = useState({ items: [], total: 0, count: 0 });

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
      .then((items) => {
        if (!cancelled) setProducts(items);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeCategory]);

  const handleAdd = useCallback(async (product) => {
    try {
      const updated = await api.addToCart(product.id, 1);
      setCart(updated);
    } catch {
      /* тихо игнорируем — состояние кнопки не меняем */
    }
  }, []);

  const cartIds = new Set(cart.items.map((i) => i.product_id));

  return (
    <>
      <Header cartCount={cart.count} onCart={() => {}} />
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
    </>
  );
}
