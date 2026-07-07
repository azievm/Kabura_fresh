import { Leaf, Plus, Check } from "lucide-react";
import { Badge } from "../components/Badge.jsx";
import { PriceTag } from "../components/PriceTag.jsx";
import { Button } from "../components/Button.jsx";
import { haptic } from "../lib/telegram.js";
import s from "./ProductDetail.module.css";

export function ProductDetail({ product, inCart, onAdd }) {
  if (!product) return null;

  function handleAdd() {
    haptic("light");
    onAdd(product);
  }

  return (
    <div className={s.screen}>
      <div className={`${s.hero} ${!product.is_available ? s.dim : ""}`}>
        {product.has_image ? (
          <img src={`/api/products/${product.id}/image`} alt={product.name} />
        ) : (
          <Leaf size={64} strokeWidth={1.3} className={s.placeholder} aria-hidden="true" />
        )}
      </div>

      <div className={s.body}>
        <h1 className={s.name}>{product.name}</h1>
        <Badge available={product.is_available} />
        <div className={s.price}>
          <PriceTag
            retail={product.retail_price}
            wholesale={product.wholesale_price}
            category={product.category}
          />
        </div>
        <p className={s.desc}>
          {product.description || "Описание скоро добавим."}
        </p>
      </div>

      <div className={s.bar}>
        <Button
          variant={inCart ? "secondary" : "primary"}
          full
          disabled={!product.is_available}
          onClick={handleAdd}
        >
          {inCart ? <Check size={18} /> : <Plus size={18} />}
          {!product.is_available ? "Нет в наличии" : inCart ? "В корзине" : "В корзину"}
        </Button>
      </div>
    </div>
  );
}
