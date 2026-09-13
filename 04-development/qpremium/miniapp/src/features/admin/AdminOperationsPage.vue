<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6 col">Операции</div>
      <q-btn flat icon="refresh" label="Обновить" @click="load" />
    </div>
    <q-banner v-if="error" class="bg-red-1 text-negative q-mb-md" rounded>{{ error }}</q-banner>
    <q-list bordered separator>
      <q-item v-for="op in items" :key="op.id">
        <q-item-section>
          <q-item-label>{{ typeLabel(op.type) }} · {{ statusLabel(op.status) }}</q-item-label>
          <q-item-label caption>
            {{ pointsText(op) }}
            <span v-if="op.purchase_amount"> · покупка {{ op.purchase_amount }} ₽</span>
            <span v-if="op.store_name_snapshot"> · {{ op.store_name_snapshot }}</span>
          </q-item-label>
          <q-item-label caption>{{ formatDt(op.created_at) }}</q-item-label>
        </q-item-section>
      </q-item>
      <q-item v-if="!items.length"><q-item-section>Операций пока нет</q-item-section></q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/shared/api";

type Op = {
  id: string;
  type: string;
  status: string;
  points: number;
  purchase_amount: string | null;
  store_name_snapshot: string;
  created_at: string;
};

const items = ref<Op[]>([]);
const error = ref("");

function typeLabel(t: string) {
  const map: Record<string, string> = {
    BONUS_ACCRUAL: "Начисление",
    BONUS_REDEMPTION: "Списание",
    GIFT_ACCRUAL: "Подарок",
    BONUS_EXPIRATION: "Сгорание",
    MANUAL_ADJUSTMENT: "Корректировка",
    REGISTRATION_GIFT: "Подарок за регистрацию",
    BIRTHDAY_GIFT: "Подарок на день рождения",
  };
  return map[t] || t;
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    PENDING: "Ожидает подтверждения",
    CONFIRMED: "Подтверждено",
    REJECTED: "Отклонено",
    CANCELLED: "Отменено",
  };
  return map[s] || s;
}

function pointsText(op: Op) {
  const n = op.points;
  if (n > 0) return `+${n} баллов`;
  if (n < 0) return `${n} баллов`;
  return "0 баллов";
}

function formatDt(iso: string) {
  try {
    return new Date(iso).toLocaleString("ru-RU", { timeZone: "Europe/Moscow" });
  } catch {
    return iso;
  }
}

async function load() {
  error.value = "";
  try {
    const data = await api<{ results: Op[] }>("/api/v1/operations");
    items.value = data.results || [];
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}
onMounted(load);
</script>
