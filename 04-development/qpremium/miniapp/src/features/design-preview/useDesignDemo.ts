import { computed, reactive, ref } from "vue";
import { api } from "@/shared/api";
import { getTelegramWebApp } from "@/shared/telegram";

export type DesignLot = { points: number; expires_at: string };
export type DesignPromo = {
  id: string;
  title: string;
  conditions_text: string;
  body_text: string;
  unit: string;
  value: string;
};

const loading = ref(true);
const firstName = ref("Гость");
const fullName = ref("Участник Q Premium");
const phone = ref("+7 —");
const email = ref("—");
const birthDate = ref("");
const pendingBirth = ref<string | null>(null);

const earned = ref(0);
const gift = ref(0);
const total = ref(0);
const earnedLots = ref<DesignLot[]>([]);
const giftLots = ref<DesignLot[]>([]);

const accrualPercent = ref("5");
const maxRedeemPercent = ref("30");
const earnedTtlDays = ref(90);
const giftTtlDays = ref(30);
const rulesText = ref("");
const promos = ref<DesignPromo[]>([]);
const promotionsText = ref("");

const nearest = computed(() => {
  const all = [
    ...earnedLots.value.map((l) => ({ ...l, kind: "earned" as const })),
    ...giftLots.value.map((l) => ({ ...l, kind: "gift" as const })),
  ].filter((l) => l.points > 0 && l.expires_at);
  if (!all.length) return null;
  all.sort((a, b) => new Date(a.expires_at).getTime() - new Date(b.expires_at).getTime());
  return all[0];
});

const SURNAME_RE =
  /(?:ов|ова|ев|ева|ёв|ёва|ин|ина|ын|ына|ский|ская|цкий|цкая|ян|янц|дзе|швили)$/i;
const PATRONYMIC_RE = /(?:ович|евич|овна|евна|ична|инична)$/i;

/** Имя для обращения: Telegram first_name → иначе из ФИО (не фамилия). */
export function extractGivenName(full: string, tgFirst?: string | null): string {
  const fromTg = (tgFirst || "").trim();
  if (fromTg) return fromTg;

  const parts = (full || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "Гость";
  if (parts.length === 1) return parts[0];

  if (parts.length >= 3 && PATRONYMIC_RE.test(parts[parts.length - 1])) {
    return parts[1];
  }
  if (SURNAME_RE.test(parts[0])) return parts[1];
  if (SURNAME_RE.test(parts[1])) return parts[0];
  return parts[0];
}

export function formatPoints(n: number) {
  return new Intl.NumberFormat("ru-RU").format(n);
}

export function formatDateShort(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      timeZone: "Europe/Moscow",
    });
  } catch {
    return iso;
  }
}

export function formatDateLong(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      timeZone: "Europe/Moscow",
    });
  } catch {
    return iso;
  }
}

export function formatBirth(iso: string) {
  if (!iso) return "—";
  return formatDateLong(iso);
}

export function daysLabel(days: number) {
  const n = Math.abs(days) % 100;
  const n1 = n % 10;
  if (n > 10 && n < 20) return `${days} дней`;
  if (n1 === 1) return `${days} день`;
  if (n1 >= 2 && n1 <= 4) return `${days} дня`;
  return `${days} дней`;
}

export function monthsApprox(days: number) {
  if (days >= 28 && days % 30 === 0) {
    const m = days / 30;
    return `${m} ${m === 1 ? "месяц" : m < 5 ? "месяца" : "месяцев"}`.toUpperCase();
  }
  return daysLabel(days).toUpperCase();
}

let loadedOnce = false;

export async function loadDesignDemo(force = false) {
  if (loadedOnce && !force) return;
  loading.value = true;
  try {
    const tgFirst = getTelegramWebApp()?.initDataUnsafe?.user?.first_name || null;

    const [me, bal, settings] = await Promise.all([
      api<{
        full_name: string;
        phone: string;
        email: string;
        birth_date: string;
        pending_birth_date?: string | null;
      }>("/api/v1/clients/me").catch(() => null),
      api<{
        earned: number;
        gift: number;
        total: number;
        earned_lots: DesignLot[];
        gift_lots: DesignLot[];
      }>("/api/v1/clients/me/balance").catch(() => null),
      api<{
        accrual_percent: string;
        max_redeem_percent: string;
        earned_ttl_days: number;
        gift_ttl_days: number;
        rules_text: string;
        promotions_text?: string;
        promotions?: DesignPromo[];
      }>("/api/v1/settings/public").catch(() => null),
    ]);

    if (me) {
      fullName.value = me.full_name || fullName.value;
      firstName.value = extractGivenName(me.full_name || "", tgFirst);
      phone.value = me.phone || phone.value;
      email.value = me.email || email.value;
      birthDate.value = me.birth_date || "";
      pendingBirth.value = me.pending_birth_date || null;
    } else if (tgFirst) {
      firstName.value = tgFirst;
    }

    if (bal) {
      earned.value = bal.earned;
      gift.value = bal.gift;
      total.value = bal.total;
      earnedLots.value = bal.earned_lots || [];
      giftLots.value = bal.gift_lots || [];
    }

    if (settings) {
      accrualPercent.value = String(settings.accrual_percent ?? accrualPercent.value);
      maxRedeemPercent.value = String(settings.max_redeem_percent ?? maxRedeemPercent.value);
      earnedTtlDays.value = Number(settings.earned_ttl_days ?? earnedTtlDays.value);
      giftTtlDays.value = Number(settings.gift_ttl_days ?? giftTtlDays.value);
      rulesText.value = settings.rules_text || "";
      promos.value = settings.promotions || [];
      promotionsText.value = settings.promotions_text || "";
    }

    loadedOnce = true;
  } finally {
    loading.value = false;
  }
}

export function useDesignDemo() {
  return reactive({
    loading,
    firstName,
    fullName,
    phone,
    email,
    birthDate,
    pendingBirth,
    earned,
    gift,
    total,
    earnedLots,
    giftLots,
    nearest,
    accrualPercent,
    maxRedeemPercent,
    earnedTtlDays,
    giftTtlDays,
    rulesText,
    promos,
    promotionsText,
  });
}
