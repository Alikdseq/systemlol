import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { api, setToken, getToken } from "@/shared/api";
import { bootTelegramUi, collectInitData, waitForTelegramWebApp } from "@/shared/telegram";

export type AppState =
  | "AUTH_LOADING"
  | "AUTHENTICATED"
  | "AUTH_EXPIRED"
  | "FORBIDDEN"
  | "NETWORK_ERROR"
  | "SERVER_ERROR";

export type Role = "NONE" | "CLIENT" | "STORE" | "ADMIN";
export type UiMode = "client" | "work";

const UI_MODE_KEY = "qp_ui_mode";

type AuthResponse = {
  access_token: string;
  expires_in: number;
  role: Role;
  store: { id: string; name: string; address: string } | null;
  user: {
    telegram_id: number;
    client_id: string | null;
    has_client_profile?: boolean;
    can_register?: boolean;
  };
};

export const useAuthStore = defineStore("auth", () => {
  const state = ref<AppState>("AUTH_LOADING");
  const role = ref<Role>("NONE");
  const telegramId = ref<number | null>(null);
  const clientId = ref<string | null>(null);
  const store = ref<AuthResponse["store"]>(null);
  const errorMessage = ref("");
  const uiMode = ref<UiMode>((localStorage.getItem(UI_MODE_KEY) as UiMode) || "work");

  const canRegister = computed(() => !clientId.value);
  const canUseClientUi = computed(() => Boolean(clientId.value));
  const canUseWorkUi = computed(() => role.value === "STORE" || role.value === "ADMIN");

  function setUiMode(mode: UiMode) {
    uiMode.value = mode;
    localStorage.setItem(UI_MODE_KEY, mode);
  }

  async function authenticate(): Promise<void> {
    state.value = "AUTH_LOADING";
    errorMessage.value = "";
    await waitForTelegramWebApp();
    bootTelegramUi();
    try {
      const initData = collectInitData();
      const data = await api<AuthResponse>("/api/v1/auth/telegram", {
        method: "POST",
        json: { init_data: initData },
        auth: false,
      });
      setToken(data.access_token);
      role.value = data.role;
      telegramId.value = data.user.telegram_id;
      clientId.value = data.user.client_id;
      store.value = data.store;
      state.value = "AUTHENTICATED";

      if (!clientId.value) {
        // профиль клиента обязателен для покупок — даже у кассира/админа
      } else if (role.value === "CLIENT") {
        setUiMode("client");
      } else if (uiMode.value === "client" && !clientId.value) {
        setUiMode("work");
      } else if (role.value === "STORE" || role.value === "ADMIN") {
        if (uiMode.value !== "client" && uiMode.value !== "work") setUiMode("work");
      }
    } catch (e: unknown) {
      const err = e as { http?: number; message?: string; code?: string };
      if (err.http === 401 || err.code === "token_expired" || err.code === "invalid_init_data") {
        setToken(null);
        state.value = "AUTH_EXPIRED";
        errorMessage.value = err.message || "Сессия недействительна";
        return;
      }
      if (!err.http) {
        state.value = "NETWORK_ERROR";
        errorMessage.value = "Нет связи с сервером";
        return;
      }
      state.value = "SERVER_ERROR";
      errorMessage.value = err.message || "Ошибка сервера";
    }
  }

  async function reauthAfterRegister(): Promise<void> {
    await authenticate();
    if (role.value === "CLIENT") {
      setUiMode("client");
    }
    // STORE/ADMIN после своей регистрации остаются в рабочем режиме, переключаются кнопкой «Мой баланс»
  }

  function homePathForRole(r: Role = role.value): string {
    if (!clientId.value) return "/register";
    if (uiMode.value === "client") return "/";
    switch (r) {
      case "CLIENT":
        return "/";
      case "STORE":
        return "/store";
      case "ADMIN":
        return "/admin";
      case "NONE":
        return "/register";
      default:
        return "/forbidden";
    }
  }

  function ensureToken(): boolean {
    return Boolean(getToken());
  }

  return {
    state,
    role,
    telegramId,
    clientId,
    store,
    errorMessage,
    uiMode,
    canRegister,
    canUseClientUi,
    canUseWorkUi,
    setUiMode,
    authenticate,
    reauthAfterRegister,
    homePathForRole,
    ensureToken,
  };
});
