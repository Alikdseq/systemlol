/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
  readonly VITE_DEV_TELEGRAM_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface TelegramWebAppUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
}

interface TelegramWebApp {
  ready: () => void;
  expand: () => void;
  initData: string;
  initDataUnsafe: { user?: TelegramWebAppUser };
  themeParams: Record<string, string>;
  colorScheme: "light" | "dark";
  viewportHeight?: number;
  viewportStableHeight?: number;
  onEvent?: (event: string, cb: () => void) => void;
  offEvent?: (event: string, cb: () => void) => void;
  MainButton: {
    text: string;
    show: () => void;
    hide: () => void;
    onClick: (cb: () => void) => void;
    offClick: (cb: () => void) => void;
  };
}

interface Window {
  Telegram?: { WebApp?: TelegramWebApp };
}
