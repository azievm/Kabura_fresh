import s from "./Button.module.css";

export function Button({
  variant = "primary",
  size = "md",
  full = false,
  className = "",
  children,
  ...rest
}) {
  const cls = [s.btn, s[variant], s[size], full ? s.full : "", className]
    .filter(Boolean)
    .join(" ");
  return (
    <button className={cls} {...rest}>
      {children}
    </button>
  );
}
