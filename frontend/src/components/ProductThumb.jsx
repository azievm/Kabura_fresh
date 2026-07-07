import { Leaf } from "lucide-react";
import s from "./ProductThumb.module.css";

// Фото товара. image_url из Telegram — это file_id (не грузится как <img>),
// поэтому реальное изображение показываем только для http(s)-ссылок, иначе —
// спокойную монохромную заглушку (без «мультяшных» эмодзи и без ложного фрукта).
export function ProductThumb({ image, name, available = true }) {
  const isUrl = typeof image === "string" && /^https?:\/\//.test(image);
  return (
    <div className={`${s.thumb} ${!available ? s.dim : ""}`}>
      {isUrl ? (
        <img src={image} alt={name} loading="lazy" />
      ) : (
        <Leaf className={s.placeholder} size={26} strokeWidth={1.75} aria-hidden="true" />
      )}
    </div>
  );
}
