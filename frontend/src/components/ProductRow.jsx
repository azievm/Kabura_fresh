import { useState } from "react";
import { Plus, Check } from "lucide-react";
import { Button } from "./Button.jsx";
import { Badge } from "./Badge.jsx";
import { PriceTag } from "./PriceTag.jsx";
import { ProductThumb } from "./ProductThumb.jsx";
import { haptic } from "../lib/telegram.js";
import s from "./ProductRow.module.css";

// Строка каталога: фото, название, наличие, цена, кнопка «В корзину».
export function ProductRow({ product, inCart, onAdd }) {
  const [justAdded, setJustAdded] = useState(false);

  async function handleAdd() {
    haptic("light");
    await onAdd(product);
    setJustAdded(true);
    setTimeout(() => setJustAdded(false), 1200);
  }

  const added = justAdded || inCart;

  return (
    <li className={s.row}>
      <ProductThumb
        image={product.image_url}
        name={product.name}
        available={product.is_available}
      />
      <div className={s.info}>
        <div className={s.name}>{product.name}</div>
        <Badge available={product.is_available} />
        <PriceTag
          retail={product.retail_price}
          wholesale={product.wholesale_price}
          category={product.category}
        />
      </div>
      <div className={s.action}>
        <Button
          size="sm"
          variant={added ? "secondary" : "primary"}
          disabled={!product.is_available}
          onClick={handleAdd}
          aria-label={`Добавить ${product.name} в корзину`}
        >
          {added ? <Check size={16} /> : <Plus size={16} />}
          {added ? "В корзине" : "В корзину"}
        </Button>
      </div>
    </li>
  );
}
