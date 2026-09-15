<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-sm">Поиск клиента</div>
    <div class="text-caption text-grey-7 q-mb-md">Введите телефон — система найдёт клиента в общей базе.</div>

    <q-banner v-if="auth.role === 'ADMIN'" class="bg-grey-2 q-mb-md" rounded>
      <div class="text-subtitle2 q-mb-sm">Магазин для операции (обязательно)</div>
      <q-select
        v-model="storeId"
        :options="storeOpts"
        dense
        outlined
        emit-value
        map-options
        label="Выберите магазин"
        @update:model-value="onStorePick"
      />
    </q-banner>

    <q-form class="q-gutter-md" @submit.prevent="lookup">
      <TgField
        v-model="phone"
        label="Телефон"
        autocomplete="tel"
        hint="+7XXXXXXXXXX / 8900… / 900…"
      />
      <q-btn
        type="submit"
        color="primary"
        :loading="loading"
        :disable="auth.role === 'ADMIN' && !storeId"
        label="Найти"
        class="full-width"
      />
    </q-form>
    <div v-if="error" class="text-negative q-mt-md">{{ error }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "@/shared/api";
import { useAuthStore } from "@/features/auth/authStore";
import { getSelectedStore, setSelectedStore } from "@/shared/storeContext";
import TgField from "@/shared/TgField.vue";

const auth = useAuthStore();
const phone = ref("");
const loading = ref(false);
const error = ref("");
const router = useRouter();
const storeId = ref(getSelectedStore()?.id || "");
const stores = ref<{ id: string; name: string; address: string }[]>([]);

const storeOpts = computed(() => stores.value.map((s) => ({ label: `${s.name}`, value: s.id })));

function onStorePick(id: string) {
  const s = stores.value.find((x) => x.id === id);
  if (s) setSelectedStore({ id: s.id, name: s.name, address: s.address });
}

async function lookup() {
  loading.value = true;
  error.value = "";
  try {
    if (auth.role === "ADMIN" && !storeId.value) {
      error.value = "Сначала выберите магазин";
      return;
    }
    const data = await api<{
      id: string;
      full_name: string;
      phone: string;
      balance: { earned: number; gift: number; total: number };
    }>("/api/v1/clients/lookup", {
      method: "POST",
      json: { phone: phone.value.trim() },
    });
    sessionStorage.setItem(`qp_client_${data.id}`, JSON.stringify(data));
    await router.push(`/store/client/${data.id}`);
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Клиент не найден";
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (auth.role !== "ADMIN") return;
  try {
    const data = await api<{ results: { id: string; name: string; address: string; is_active: boolean }[] }>(
      "/api/v1/stores",
    );
    stores.value = (data.results || []).filter((s) => s.is_active);
    if (storeId.value) onStorePick(storeId.value);
    else if (stores.value[0]) {
      storeId.value = stores.value[0].id;
      onStorePick(storeId.value);
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Не удалось загрузить магазины";
  }
});
</script>
