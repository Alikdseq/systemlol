<template>
  <q-page class="q-pa-md">
    <q-btn flat icon="arrow_back" :to="`/store/client/${id}`" label="Назад" class="q-mb-md" />
    <div class="text-h6 q-mb-md">Списание</div>
    <q-banner class="bg-grey-2 q-mb-md" rounded>
      Сначала «Рассчитать», затем подтвердите. Количество баллов вводит система, не кассир.
    </q-banner>
    <q-form class="q-gutter-md" @submit.prevent="preview">
      <q-input
        v-model="amount"
        type="text"
        inputmode="decimal"
        label="Сумма покупки, ₽"
        outlined
        stack-label
      />
      <q-btn type="submit" color="secondary" :loading="loadingPreview" label="Рассчитать" class="full-width" />
    </q-form>

    <div v-if="previewData" class="q-mt-lg">
      <div class="text-subtitle2">Будет списано: {{ previewData.to_redeem }} баллов</div>
      <div class="text-caption">доступно {{ previewData.available }}, лимит % {{ previewData.max_by_percent }}</div>
      <q-banner v-if="mismatch" class="bg-orange-1 q-mt-md" rounded>
        Баланс изменился. Будет списано {{ appliedToRedeem }}.
      </q-banner>
      <q-btn
        class="q-mt-md full-width"
        color="primary"
        :loading="loadingApply"
        :disable="loadingApply"
        label="Подтвердить списание"
        @click="apply"
      />
    </div>
    <div v-if="error" class="text-negative q-mt-md">{{ error }}</div>
    <div v-if="done" class="text-positive q-mt-md">Списано {{ appliedToRedeem }} баллов</div>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute } from "vue-router";
import { api, newIdempotencyKey } from "@/shared/api";
import { useAuthStore } from "@/features/auth/authStore";
import { storeIdForWrite } from "@/shared/storeContext";

const route = useRoute();
const auth = useAuthStore();
const id = route.params.id as string;
const amount = ref("");
const loadingPreview = ref(false);
const loadingApply = ref(false);
const error = ref("");
const done = ref(false);
const mismatch = ref(false);
const appliedToRedeem = ref<number | null>(null);
const previewData = ref<{ to_redeem: number; available: number; max_by_percent: number } | null>(null);
let idemKey = newIdempotencyKey();

function purchaseAmount() {
  return amount.value.replace(",", ".");
}

async function preview() {
  loadingPreview.value = true;
  error.value = "";
  done.value = false;
  mismatch.value = false;
  try {
    previewData.value = await api("/api/v1/redemptions/preview", {
      method: "POST",
      json: { client_id: id, purchase_amount: purchaseAmount() },
    });
    idemKey = newIdempotencyKey();
  } catch (e: unknown) {
    previewData.value = null;
    error.value = (e as { message?: string }).message || "Ошибка preview";
  } finally {
    loadingPreview.value = false;
  }
}

async function apply() {
  if (!previewData.value) return;
  loadingApply.value = true;
  error.value = "";
  try {
    const storeId = storeIdForWrite(auth.role);
    if (auth.role === "ADMIN" && !storeId) {
      error.value = "Выберите магазин на экране кассы";
      return;
    }
    const payload: Record<string, string> = {
      client_id: id,
      purchase_amount: purchaseAmount(),
    };
    if (storeId) payload.store_id = storeId;

    const data = await api<{ to_redeem: number }>("/api/v1/redemptions", {
      method: "POST",
      headers: { "Idempotency-Key": idemKey },
      json: payload,
    });
    appliedToRedeem.value = data.to_redeem;
    if (data.to_redeem !== previewData.value.to_redeem) mismatch.value = true;
    done.value = true;
    idemKey = newIdempotencyKey();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка списания";
  } finally {
    loadingApply.value = false;
  }
}
</script>
