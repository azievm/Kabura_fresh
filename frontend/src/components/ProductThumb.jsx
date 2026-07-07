import { Leaf } from "lucide-react";
import s from "./ProductThumb.module.css";

// Фото товара. Реальное фото грузим через прокси /api/products/{id}/image
// (Telegram file_id нельзя вставить в <img> напрямую). Нет фото — спокойная
// монохромная заглушка (без «мультяшных» эмодзи).
export function ProductThumb({ productId, hasImage, name, available = true }) {
  return (
    <div className={`${s.thumb} ${!available ? s.dim : ""}`}>
      {hasImage ? (
        <img src={`/api/products/${productId}/image`} alt={name} loading="lazy" />
      ) : (
        <Leaf className={s.placeholder} size={26} strokeWidth={1.75} aria-hidden="true" />
      )}
    </div>
  );
}
