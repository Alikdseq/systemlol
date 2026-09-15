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
      <TgField v-model="amount" label="Сумма покупки, ₽" />
      <div v-if="error" class="text-negative">{{ error }}</div>
      <q-btn
        type="submit"
        color="primary"
        class="full-width"
        :loading="loading"
        :disable="loading || done"
        :label="auth.role === 'ADMIN' ? 'Начислить сразу' : 'Отправить на подтверждение'"
      />
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Notify } from "quasar";
import { api, newIdempotencyKey } from "@/shared/api";
import { useAuthStore } from "@/features/auth/authStore";
import { storeIdForWrite } from "@/shared/storeContext";
import TgField from "@/shared/TgField.vue";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const id = route.params.id as string;
const amount = ref("");
const loading = ref(false);
const done = ref(false);
const error = ref("");
let idemKey = newIdempotencyKey();

async function submit() {
  if (loading.value || done.value) return;
  loading.value = true;
  error.value = "";
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
    done.value = true;
    const msg =
      data.status === "CONFIRMED" || auth.role === "ADMIN"
        ? `Начислено ${data.points} баллов`
        : `Отправлено на подтверждение: ${data.points} баллов`;
    Notify.create({ type: "positive", message: msg, timeout: 2500 });
    await router.replace("/store");
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
    idemKey = newIdempotencyKey();
  } finally {
    loading.value = false;
  }
}
</script>
