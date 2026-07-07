// Обёртка над Telegram WebApp SDK (загружается в index.html).
export const tg = typeof window !== "undefined" ? window.Telegram?.WebApp : undefined;

export const initData = tg?.initData || "";

// Синхронизируем тему приложения с темой Telegram (для наших data-theme токенов).
function applyTheme() {
  if (!tg) return;
  document.documentElement.dataset.theme = tg.colorScheme === "dark" ? "dark" : "light";
}

export function initTelegram() {
  if (!tg) {
    // Вне Telegram (обычный браузер) — светлая тема по умолчанию.
    document.documentElement.dataset.theme = "light";
    return;
  }
  tg.ready();
  tg.expand();
  applyTheme();
  tg.onEvent("themeChanged", applyTheme);
}

// Тактильная отдача (если поддерживается).
export function haptic(type = "light") {
  try {
    tg?.HapticFeedback?.impactOccurred(type);
  } catch {
    /* no-op */
  }
}
