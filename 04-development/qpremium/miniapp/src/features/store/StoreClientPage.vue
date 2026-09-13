<template>
  <q-page class="q-pa-md">
    <q-btn flat icon="arrow_back" label="Назад" to="/store" class="q-mb-md" />
    <div class="text-h6">{{ client?.full_name || "Клиент" }}</div>
    <div class="text-body2 text-grey-7 q-mb-md">{{ client?.phone }}</div>
    <div class="row q-col-gutter-sm q-mb-lg">
      <div class="col-4"><div class="text-caption">Накоп.</div><div class="text-h6">{{ client?.balance.earned }}</div></div>
      <div class="col-4"><div class="text-caption">Подар.</div><div class="text-h6">{{ client?.balance.gift }}</div></div>
      <div class="col-4"><div class="text-caption">Всего</div><div class="text-h6">{{ client?.balance.total }}</div></div>
    </div>
    <div class="column q-gutter-sm">
      <q-btn color="primary" :to="`/store/accrual/${id}`" label="Начислить" />
      <q-btn color="secondary" :to="`/store/redeem/${id}`" label="Списать" />
    </div>
    <div v-if="error" class="text-negative q-mt-md">{{ error }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "@/shared/api";

const route = useRoute();
const id = route.params.id as string;
const error = ref("");
const client = ref<{
  id: string;
  full_name: string;
  phone: string;
  balance: { earned: number; gift: number; total: number };
} | null>(null);

onMounted(async () => {
  // lookup by id: use admin card if ADMIN else re-lookup is phone-only — use clients/{id} for ADMIN,
  // for STORE we already came from lookup; refetch via phone not available.
  // Store keeps data via a lightweight sessionStorage stash from lookup, fallback admin endpoint.
  try {
    const cached = sessionStorage.getItem(`qp_client_${id}`);
    if (cached) {
      client.value = JSON.parse(cached);
      return;
    }
    client.value = await api(`/api/v1/clients/${id}`);
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Не удалось загрузить клиента";
  }
});
</script>
