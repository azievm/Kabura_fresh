import { CategoryChips } from "../components/CategoryChips.jsx";
import { ProductRow } from "../components/ProductRow.jsx";
import s from "./Catalog.module.css";

export function Catalog({
  categories,
  activeCategory,
  onCategoryChange,
  products,
  loading,
  error,
  cartIds,
  onAdd,
}) {
  return (
    <div className={s.screen}>
      <div className={s.chips}>
        <CategoryChips
          categories={categories}
          active={activeCategory}
          onChange={onCategoryChange}
        />
      </div>

      {loading && (
        <ul className={s.list} aria-busy="true">
          {Array.from({ length: 5 }).map((_, i) => (
            <li key={i} className={s.skeleton} />
          ))}
        </ul>
      )}

      {!loading && error && (
        <div className={s.state}>
          <p>Не удалось загрузить товары.</p>
          <p className={s.muted}>Проверьте связь и попробуйте ещё раз.</p>
        </div>
      )}

      {!loading && !error && products.length === 0 && (
        <div className={s.state}>
          <p>В этой категории пока нет товаров.</p>
        </div>
      )}

      {!loading && !error && products.length > 0 && (
        <ul className={s.list}>
          {products.map((p) => (
            <ProductRow
              key={p.id}
              product={p}
              inCart={cartIds.has(p.id)}
              onAdd={onAdd}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
