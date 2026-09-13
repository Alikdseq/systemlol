<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-dark text-dark-pink">
      <q-toolbar>
        <q-toolbar-title>Регистрация в Q Premium</q-toolbar-title>
      </q-toolbar>
    </q-header>
    <q-page-container>
      <q-page class="q-pa-md">
        <div class="text-body2 text-grey-7 q-mb-md">
          Заполните данные один раз. Обязательное согласие — по 152‑ФЗ и правилам программы.
        </div>
        <q-form class="q-gutter-md" @submit.prevent="submit">
          <q-input
            v-model="form.full_name"
            label="ФИО"
            outlined
            stack-label
            :rules="[req]"
            autocomplete="name"
          />
          <q-input
            v-model="form.phone"
            type="text"
            inputmode="tel"
            autocomplete="tel"
            label="Телефон"
            hint="Можно 8900…, +7900…, 900… — система приведёт к единому виду"
            outlined
            stack-label
            :rules="[req]"
          />
          <q-input
            v-model="form.email"
            type="email"
            inputmode="email"
            autocomplete="email"
            label="Email"
            outlined
            stack-label
            :rules="[req]"
          />
          <q-input
            v-model="form.birth_date"
            type="date"
            label="Дата рождения"
            outlined
            stack-label
            :rules="[req]"
          />

          <q-checkbox
            v-model="form.rulesAndPersonal"
            label="Принимаю правила программы лояльности и даю согласие на обработку персональных данных (152‑ФЗ) *"
          />
          <q-checkbox
            v-model="form.advertising"
            label="Согласен получать рекламные сообщения (необязательно, для рассылок)"
          />

          <div v-if="error" class="text-negative text-body2">{{ error }}</div>
          <q-btn type="submit" color="primary" class="full-width" :loading="loading" label="Зарегистрироваться" />
        </q-form>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { api, getToken } from "@/shared/api";
import { useAuthStore } from "@/features/auth/authStore";

const auth = useAuthStore();
const router = useRouter();
const loading = ref(false);
const error = ref("");

const form = reactive({
  full_name: "",
  phone: "",
  email: "",
  birth_date: "",
  rulesAndPersonal: false,
  advertising: false,
});

const req = (v: string) => (!!v && String(v).trim().length > 0) || "Обязательное поле";

onMounted(async () => {
  // Гарантируем свежий Bearer до сабмита (иначе DRF: «учетные данные не были предоставлены»)
  if (!getToken()) {
    await auth.authenticate();
  }
});

async function submit() {
  error.value = "";
  if (!form.rulesAndPersonal) {
    error.value = "Нужно принять правила и согласие на обработку персональных данных";
    return;
  }
  loading.value = true;
  try {
    if (!getToken()) {
      await auth.authenticate();
    }
    if (!getToken()) {
      error.value = "Нет сессии. Закройте Mini App и откройте снова через бота.";
      return;
    }
    await api("/api/v1/clients/register", {
      method: "POST",
      json: {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim(),
        birth_date: form.birth_date,
        consents: {
          RULES_AND_PERSONAL_DATA: true,
          PROGRAM_RULES: true,
          PERSONAL_DATA: true,
          ADVERTISING: form.advertising,
        },
      },
    });
    await auth.reauthAfterRegister();
    await router.replace(auth.homePathForRole());
  } catch (e: unknown) {
    const err = e as { message?: string; http?: number };
    if (err.http === 401) {
      await auth.authenticate();
      error.value = "Сессия обновилась. Нажмите «Зарегистрироваться» ещё раз.";
    } else {
      error.value = err.message || "Не удалось зарегистрироваться";
    }
  } finally {
    loading.value = false;
  }
}
</script>
