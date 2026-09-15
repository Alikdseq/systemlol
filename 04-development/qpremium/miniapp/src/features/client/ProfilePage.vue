<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Профиль</div>
    <q-form class="q-gutter-md" @submit.prevent="save">
      <TgField v-model="form.full_name" label="ФИО" autocomplete="name" />
      <TgField v-model="form.phone" label="Телефон" autocomplete="tel" />
      <TgField v-model="form.email" label="Email" autocomplete="email" />
      <TgField v-model="form.birth_date" label="Дата рождения" type="date" />
      <q-banner v-if="pendingBirth && auth.role !== 'ADMIN'" class="bg-orange-1" rounded>
        Запрос на смену даты рождения на {{ pendingBirth }} ожидает подтверждения администратора.
      </q-banner>
      <div v-else-if="auth.role === 'ADMIN'" class="text-caption text-grey-7">
        Для администратора дата рождения сохраняется сразу, без подтверждения.
      </div>

      <q-card flat bordered>
        <q-card-section class="row items-center">
          <div class="col">
            <div class="text-subtitle2">Рекламные сообщения</div>
            <div class="text-caption text-grey-7">
              {{ advertising ? "Включено: можно присылать акции и новости" : "Выключено: рассылки не приходят" }}
            </div>
            <a href="#" class="text-caption text-primary" @click.prevent="advDoc = true">Текст согласия на рекламу (38‑ФЗ)</a>
          </div>
          <q-toggle
            v-model="advertising"
            color="primary"
            :disable="advBusy"
            @update:model-value="toggleAdvertising"
          />
        </q-card-section>
      </q-card>
      <a href="#" class="text-caption text-primary" @click.prevent="privacyDoc = true">Политика обработки персональных данных</a>

      <LegalDocDialog v-model="advDoc" slug="advertising" />
      <LegalDocDialog v-model="privacyDoc" slug="privacy" />

      <div v-if="error" class="text-negative">{{ error }}</div>
      <div v-if="ok" class="text-positive">{{ ok }}</div>
      <q-btn type="submit" color="primary" :loading="loading" label="Сохранить" />
    </q-form>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { api } from "@/shared/api";
import { useAuthStore } from "@/features/auth/authStore";
import LegalDocDialog from "@/shared/LegalDocDialog.vue";
import TgField from "@/shared/TgField.vue";

const auth = useAuthStore();
const form = reactive({ full_name: "", phone: "", email: "", birth_date: "" });
const advertising = ref(false);
const advDoc = ref(false);
const privacyDoc = ref(false);
const pendingBirth = ref<string | null>(null);
const loading = ref(false);
const advBusy = ref(false);
const error = ref("");
const ok = ref("");

async function load() {
  const data = await api<{
    full_name: string;
    phone: string;
    email: string;
    birth_date: string;
    advertising_accepted?: boolean;
    pending_birth_date?: string | null;
  }>("/api/v1/clients/me");
  form.full_name = data.full_name;
  form.phone = data.phone;
  form.email = data.email;
  form.birth_date = data.birth_date;
  advertising.value = Boolean(data.advertising_accepted);
  pendingBirth.value = data.pending_birth_date || null;
}

async function toggleAdvertising(val: boolean) {
  advBusy.value = true;
  error.value = "";
  ok.value = "";
  try {
    const res = await api<{ advertising_accepted: boolean }>("/api/v1/clients/me/advertising", {
      method: "POST",
      json: { accepted: val },
    });
    advertising.value = res.advertising_accepted;
    ok.value = res.advertising_accepted
      ? "Согласие на рекламу включено"
      : "Рекламные сообщения отключены";
  } catch (e: unknown) {
    advertising.value = !val;
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    advBusy.value = false;
  }
}

async function save() {
  loading.value = true;
  error.value = "";
  ok.value = "";
  try {
    const res = await api<{ note?: string; pending_birth_date?: string | null }>(
      "/api/v1/clients/me",
      { method: "PATCH", json: { ...form } },
    );
    ok.value = res.note || "Сохранено";
    pendingBirth.value = res.pending_birth_date || null;
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  load().catch((e) => {
    error.value = (e as { message?: string }).message || "Ошибка загрузки";
  });
});
</script>
