<template>
  <q-page class="q-pa-md">
    <q-btn flat icon="arrow_back" :to="`/store/client/${id}`" label="Назад" class="q-mb-md" />
    <div class="text-h6 q-mb-md">Начисление</div>
    <q-banner class="bg-grey-2 q-mb-md" rounded>
      <template v-if="auth.role === 'ADMIN'">
        Введите сумму покупки. Баллы посчитает сервер и начислит сразу (без очереди подтверждения).
      </template>
      <template v-else>
        Введите только сумму покупки. Баллы посчитает сервер. После отправки — статус PENDING (ждёт админа).
      </template>
    </q-banner>
    <q-form class="q-gutter-md" @submit.prevent="submit">
      <q-input
        v-model="amount"
        type="text"
        inputmode="decimal"
        label="Сумма покупки, ₽"
        outlined
        stack-label
      />
      <div v-if="error" class="text-negative">{{ error }}</div>
      <div v-if="result" class="text-positive">
        <template v-if="result.status === 'CONFIRMED'">
          Начислено сразу: {{ result.points }} баллов. Клиент получит уведомление.
        </template>
        <template v-else>
          Создано PENDING: {{ result.points }} баллов — подтвердите в разделе «Ожидают».
        </template>
      </div>
      <q-btn
        type="submit"
        color="primary"
        class="full-width"
        :loading="loading"
        :disable="loading"
        :label="auth.role === 'ADMIN' ? 'Начислить сразу' : 'Отправить на подтверждение'"
      />
    </q-form>
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
const loading = ref(false);
const error = ref("");
const result = ref<{ points: number; status?: string } | null>(null);
let idemKey = newIdempotencyKey();

async function submit() {
  loading.value = true;
  error.value = "";
  result.value = null;
  try {
    const storeId = storeIdForWrite(auth.role);
    if (auth.role === "ADMIN" && !storeId) {
      error.value = "Выберите магазин на экране кассы";
      return;
    }
    const payload: Record<string, string> = {
      client_id: id,
      purchase_amount: amount.value.replace(",", "."),
    };
    if (storeId) payload.store_id = storeId;

    const data = await api<{ points: number; status?: string }>("/api/v1/accruals", {
      method: "POST",
      headers: { "Idempotency-Key": idemKey },
      json: payload,
    });
    result.value = data;
    idemKey = newIdempotencyKey();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    loading.value = false;
  }
}
</script>
