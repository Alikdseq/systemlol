<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Правила программы</div>
    <q-list bordered separator class="q-mb-md">
      <q-item><q-item-section>Начисление</q-item-section><q-item-section side>{{ s?.accrual_percent }}%</q-item-section></q-item>
      <q-item><q-item-section>Макс. списание</q-item-section><q-item-section side>{{ s?.max_redeem_percent }}%</q-item-section></q-item>
      <q-item><q-item-section>Мин. сумма</q-item-section><q-item-section side>{{ s?.min_purchase_amount }} ₽</q-item-section></q-item>
      <q-item><q-item-section>Срок накопительных</q-item-section><q-item-section side>{{ s?.earned_ttl_days }} дн.</q-item-section></q-item>
      <q-item><q-item-section>Срок подарочных</q-item-section><q-item-section side>{{ s?.gift_ttl_days }} дн.</q-item-section></q-item>
    </q-list>
    <div class="text-body1" style="white-space: pre-wrap">{{ s?.rules_text || "Текст правил пока не задан администратором." }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/shared/api";

type Settings = {
  accrual_percent: string;
  max_redeem_percent: string;
  min_purchase_amount: string;
  earned_ttl_days: number;
  gift_ttl_days: number;
  rules_text: string;
};

const s = ref<Settings | null>(null);
onMounted(async () => {
  s.value = await api<Settings>("/api/v1/settings/public");
});
</script>
