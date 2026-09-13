/** Telegram WebApp helpers + browser/dev fallback (08_ boot). */

export function getTelegramWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

/** Wait for defer-loaded telegram-web-app.js (max ~1.2s), then read initData. */
export async function waitForTelegramWebApp(maxMs = 1200): Promise<TelegramWebApp | null> {
  const started = Date.now();
  let wa = getTelegramWebApp();
  while (!wa && Date.now() - started < maxMs) {
    await new Promise((r) => setTimeout(r, 40));
    wa = getTelegramWebApp();
  }
  if (!wa) return null;
  // initData иногда появляется на тик позже ready()
  if (!wa.initData) {
    const until = Date.now() + 400;
    while (!wa.initData && Date.now() < until) {
      await new Promise((r) => setTimeout(r, 40));
    }
  }
  return wa;
}

export function collectInitData(): string {
  const wa = getTelegramWebApp();
  if (wa?.initData) return wa.initData;

  // Dev outside Telegram: только если backend ALLOW_DEV_AUTH=1 и DEBUG=1
  const devId = import.meta.env.VITE_DEV_TELEGRAM_ID || "900001";
  return JSON.stringify({ id: Number(devId) });
}

function scrollFocusedIntoView(): void {
  const el = document.activeElement as HTMLElement | null;
  if (!el) return;
  const tag = (el.tagName || "").toLowerCase();
  if (tag !== "input" && tag !== "textarea" && tag !== "select") return;
  // После открытия клавиатуры WebView пересчитывает высоту
  window.setTimeout(() => {
    try {
      el.scrollIntoView({ block: "center", behavior: "smooth", inline: "nearest" });
    } catch {
      el.scrollIntoView(true);
    }
  }, 120);
}

export function bootTelegramUi(): void {
  const wa = getTelegramWebApp();
  if (!wa) return;

  wa.ready();
  wa.expand();

  // Меньше конфликтов скролла с клавиатурой (Bot API 7+)
  try {
    const anyWa = wa as TelegramWebApp & {
      disableVerticalSwipes?: () => void;
      isVerticalSwipesEnabled?: boolean;
    };
    if (typeof anyWa.disableVerticalSwipes === "function") {
      anyWa.disableVerticalSwipes();
    } else if ("isVerticalSwipesEnabled" in anyWa) {
      anyWa.isVerticalSwipesEnabled = false;
    }
  } catch {
    /* older clients */
  }

  // CSS var для высоты viewport Mini App
  const applyH = () => {
    const h = wa.viewportStableHeight || wa.viewportHeight || window.innerHeight;
    document.documentElement.style.setProperty("--tg-viewport-stable-height", `${h}px`);
  };
  applyH();
  wa.onEvent?.("viewportChanged", applyH);

  document.addEventListener("focusin", scrollFocusedIntoView, true);
}
