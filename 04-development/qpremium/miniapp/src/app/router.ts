import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/features/auth/authStore";

/** Lazy pages — initial chunk = boot + auth only (Telegram Mini App cold start). */
const routes: RouteRecordRaw[] = [
  {
    path: "/boot",
    name: "boot",
    component: () => import("@/features/auth/BootPage.vue"),
  },
  {
    path: "/register",
    name: "register",
    component: () => import("@/features/auth/RegisterPage.vue"),
    meta: { needRegister: true },
  },
  {
    path: "/forbidden",
    name: "forbidden",
    component: () => import("@/features/auth/ForbiddenPage.vue"),
  },
  {
    path: "/",
    component: () => import("@/app/layouts/ClientLayout.vue"),
    meta: { needClient: true },
    children: [
      { path: "", name: "balance", component: () => import("@/features/client/BalancePage.vue") },
      { path: "profile", name: "profile", component: () => import("@/features/client/ProfilePage.vue") },
      { path: "rules", name: "rules", component: () => import("@/features/client/RulesPage.vue") },
      { path: "promos", name: "promos", component: () => import("@/features/client/PromosPage.vue") },
    ],
  },
  {
    path: "/store",
    component: () => import("@/app/layouts/StoreLayout.vue"),
    meta: { needWork: true, workRoles: ["STORE", "ADMIN"] },
    children: [
      { path: "", name: "store-home", component: () => import("@/features/store/StoreHomePage.vue") },
      {
        path: "client/:id",
        name: "store-client",
        component: () => import("@/features/store/StoreClientPage.vue"),
      },
      {
        path: "accrual/:id",
        name: "store-accrual",
        component: () => import("@/features/store/StoreAccrualPage.vue"),
      },
      {
        path: "redeem/:id",
        name: "store-redeem",
        component: () => import("@/features/store/StoreRedeemPage.vue"),
      },
    ],
  },
  {
    path: "/design-preview",
    component: () => import("@/features/design-preview/DesignPreviewShell.vue"),
    meta: { needWork: true, workRoles: ["ADMIN"], designPreview: true },
    children: [
      { path: "", redirect: { name: "design-balance" } },
      {
        path: "balance",
        name: "design-balance",
        component: () => import("@/features/design-preview/DesignBalancePage.vue"),
      },
      {
        path: "promos",
        name: "design-promos",
        component: () => import("@/features/design-preview/DesignPromosPage.vue"),
      },
      {
        path: "rules",
        name: "design-rules",
        component: () => import("@/features/design-preview/DesignRulesPage.vue"),
      },
      {
        path: "data",
        name: "design-data",
        component: () => import("@/features/design-preview/DesignDataPage.vue"),
      },
    ],
  },
  {
    path: "/admin",
    component: () => import("@/app/layouts/AdminLayout.vue"),
    meta: { needWork: true, workRoles: ["ADMIN"] },
    children: [
      { path: "", name: "admin-home", component: () => import("@/features/admin/AdminHomePage.vue") },
      {
        path: "pending",
        name: "admin-pending",
        component: () => import("@/features/admin/AdminPendingPage.vue"),
      },
      {
        path: "clients",
        name: "admin-clients",
        component: () => import("@/features/admin/AdminClientsPage.vue"),
      },
      {
        path: "clients/:id",
        name: "admin-client",
        component: () => import("@/features/admin/AdminClientDetailPage.vue"),
      },
      {
        path: "operations",
        name: "admin-operations",
        component: () => import("@/features/admin/AdminOperationsPage.vue"),
      },
      {
        path: "stores",
        name: "admin-stores",
        component: () => import("@/features/admin/AdminStoresPage.vue"),
      },
      { path: "stats", name: "admin-stats", component: () => import("@/features/admin/AdminStatsPage.vue") },
      {
        path: "broadcasts",
        name: "admin-broadcasts",
        component: () => import("@/features/admin/AdminBroadcastsPage.vue"),
      },
      {
        path: "settings",
        name: "admin-settings",
        component: () => import("@/features/admin/AdminSettingsPage.vue"),
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory("/app/"),
  routes,
});

let bootPromise: Promise<void> | null = null;

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.name === "boot") return true;

  if (auth.state === "AUTHENTICATED" && auth.ensureToken()) {
    // already signed in
  } else if (auth.state === "AUTH_LOADING" || !auth.ensureToken()) {
    bootPromise ??= auth.authenticate();
    await bootPromise;
    bootPromise = null;
  }

  if (auth.state === "AUTH_EXPIRED" || auth.state === "NETWORK_ERROR" || auth.state === "SERVER_ERROR") {
    if (to.name !== "boot") return { name: "boot" };
    return true;
  }

  // Нет клиентского профиля → регистрация (для всех ролей)
  if (!auth.clientId && to.name !== "register") {
    return { name: "register" };
  }
  if (to.meta.needRegister && auth.clientId) {
    return auth.homePathForRole();
  }

  if (to.meta.needClient) {
    if (!auth.clientId) return { name: "register" };
    // Кассир/админ в режиме «работа» не видят клиентский UI, пока не переключатся
    if (auth.canUseWorkUi && auth.uiMode === "work" && (auth.role === "STORE" || auth.role === "ADMIN")) {
      return auth.homePathForRole();
    }
    return true;
  }

  if (to.meta.needWork) {
    const roles = (to.meta.workRoles as string[]) || [];
    if (!roles.includes(auth.role)) return { name: "forbidden" };
    if (auth.uiMode === "client") {
      auth.setUiMode("work");
    }
    return true;
  }

  return true;
});
