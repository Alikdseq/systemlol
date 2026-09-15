<template>
  <q-page class="q-pa-md balance-page">
    <div class="text-h6 q-mb-md">Мой баланс</div>
    <q-banner v-if="error" class="bg-red-1 text-negative q-mb-md">{{ error }}</q-banner>
    <q-inner-loading :showing="loading" />

    <div class="balance-totals q-mb-lg">
      <div class="balance-total">
        <div class="balance-total__label">Накопительные</div>
        <div class="balance-total__value">{{ balance?.earned ?? "—" }}</div>
      </div>
      <div class="balance-total">
        <div class="balance-total__label">Подарочные</div>
        <div class="balance-total__value">{{ balance?.gift ?? "—" }}</div>
      </div>
      <div class="balance-total balance-total--all">
        <div class="balance-total__label">Всего</div>
        <div class="balance-total__value">{{ balance?.total ?? "—" }}</div>
      </div>
    </div>

    <section class="balance-section">
      <header class="balance-section__head">
        <div class="balance-section__title">Накопительные</div>
        <div class="balance-section__sub">даты сгорания</div>
      </header>
      <div v-if="(balance?.earned_lots || []).length" class="balance-lots">
        <div v-for="(lot, i) in balance?.earned_lots" :key="'e' + i" class="balance-lot">
          <span class="balance-lot__points">{{ lot.points }}</span>
          <span class="balance-lot__sep">·</span>
          <span class="balance-lot__until">до {{ formatDate(lot.expires_at) }}</span>
        </div>
      </div>
      <div v-else class="balance-empty">Пока нет накопительных баллов</div>
    </section>

    <section class="balance-section">
      <header class="balance-section__head">
        <div class="balance-section__title">Подарочные</div>
        <div class="balance-section__sub">даты сгорания</div>
      </header>
      <div v-if="(balance?.gift_lots || []).length" class="balance-lots">
        <div v-for="(lot, i) in balance?.gift_lots" :key="'g' + i" class="balance-lot">
          <span class="balance-lot__points">{{ lot.points }}</span>
          <span class="balance-lot__sep">·</span>
          <span class="balance-lot__until">до {{ formatDate(lot.expires_at) }}</span>
        </div>
      </div>
      <div v-else class="balance-empty">Пока нет подарочных баллов</div>
    </section>

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
};

const balance = ref<Balance | null>(null);
const loading = ref(false);
const error = ref("");

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
      timeZone: "Europe/Moscow",
    });
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
