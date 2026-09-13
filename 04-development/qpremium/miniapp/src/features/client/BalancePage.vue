<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Мой баланс</div>
    <q-banner v-if="error" class="bg-red-1 text-negative q-mb-md">{{ error }}</q-banner>
    <q-inner-loading :showing="loading" />

    <div class="row q-col-gutter-md q-mb-lg">
      <div class="col-4">
        <div class="text-caption text-grey-7">Накопительные</div>
        <div class="text-h5">{{ balance?.earned ?? "—" }}</div>
      </div>
      <div class="col-4">
        <div class="text-caption text-grey-7">Подарочные</div>
        <div class="text-h5">{{ balance?.gift ?? "—" }}</div>
      </div>
      <div class="col-4">
        <div class="text-caption text-grey-7">Всего</div>
        <div class="text-h5 text-weight-bold">{{ balance?.total ?? "—" }}</div>
      </div>
    </div>

    <div class="text-subtitle2 q-mb-sm">Ближайшие сгорания</div>
    <q-list bordered separator v-if="(balance?.nearest_expirations || []).length">
      <q-item v-for="(row, i) in balance?.nearest_expirations" :key="i">
        <q-item-section>
          <q-item-label>
            {{ row.date }} · {{ row.point_type_label || pointTypeRu(row.point_type) }}
          </q-item-label>
          <q-item-label caption>{{ row.points }} баллов</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
    <div v-else class="text-body2 text-grey-7">Нет ближайших сгораний</div>

    <div class="text-subtitle2 q-mt-lg q-mb-sm">Партии: накопительные</div>
    <q-list bordered separator dense>
      <q-item v-for="(lot, i) in balance?.earned_lots || []" :key="'e' + i">
        <q-item-section>{{ lot.points }} · до {{ formatDt(lot.expires_at) }}</q-item-section>
      </q-item>
      <q-item v-if="!(balance?.earned_lots || []).length"><q-item-section class="text-grey">пусто</q-item-section></q-item>
    </q-list>

    <div class="text-subtitle2 q-mt-lg q-mb-sm">Партии: подарочные</div>
    <q-list bordered separator dense>
      <q-item v-for="(lot, i) in balance?.gift_lots || []" :key="'g' + i">
        <q-item-section>{{ lot.points }} · до {{ formatDt(lot.expires_at) }}</q-item-section>
      </q-item>
      <q-item v-if="!(balance?.gift_lots || []).length"><q-item-section class="text-grey">пусто</q-item-section></q-item>
    </q-list>

    <q-btn class="q-mt-lg" flat color="primary" label="Обновить" @click="load" />
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/shared/api";

type Balance = {
  earned: number;
  gift: number;
  total: number;
  earned_lots: { expires_at: string; points: number }[];
  gift_lots: { expires_at: string; points: number }[];
  nearest_expirations: {
    date: string;
    points: number;
    point_type: string;
    point_type_label?: string;
  }[];
};

const balance = ref<Balance | null>(null);
const loading = ref(false);
const error = ref("");

function pointTypeRu(t: string) {
  if (t === "gift") return "подарочные";
  if (t === "earned") return "накопительные";
  return t;
}

function formatDt(iso: string) {
  try {
    return new Date(iso).toLocaleString("ru-RU", { timeZone: "Europe/Moscow" });
  } catch {
    return iso;
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    balance.value = await api<Balance>("/api/v1/clients/me/balance");
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка загрузки";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>
