<template>
  <div class="register-page">
    <header class="register-head">Регистрация в Q Premium</header>
    <div class="q-pa-md">
        <div class="text-body2 text-grey-7 q-mb-md">
          Заполните данные один раз. Откройте и прочитайте тексты согласий до отметки — это требование 152‑ФЗ и закона о рекламе.
        </div>
        <q-form class="q-gutter-md" @submit.prevent="submit">
          <TgField v-model="form.full_name" label="ФИО" autocomplete="name" />
          <TgField
            v-model="form.phone"
            label="Телефон"
            autocomplete="tel"
            hint="Можно 8900…, +7900…, 900… — система приведёт к единому виду"
          />
          <TgField v-model="form.email" label="Email" autocomplete="email" />
          <TgField v-model="form.birth_date" label="Дата рождения" type="date" />

          <q-checkbox v-model="form.programRules">
            <span>
              Принимаю
              <a href="#" class="text-primary" @click.prevent="openDoc('program-rules')">правила программы лояльности</a>
              *
            </span>
          </q-checkbox>
          <q-checkbox v-model="form.personalData">
            <span>
              Даю согласие на
              <a href="#" class="text-primary" @click.prevent="openDoc('personal-data')">обработку персональных данных</a>
              и подтверждаю, что ознакомлен(а) с
              <a href="#" class="text-primary" @click.prevent="openDoc('privacy')">политикой конфиденциальности</a>
              (152‑ФЗ) *
            </span>
          </q-checkbox>
          <q-checkbox v-model="form.advertising">
            <span>
              Согласен(на) получать
              <a href="#" class="text-primary" @click.prevent="openDoc('advertising')">рекламу в Telegram-боте</a>
              (необязательно, на участие в программе не влияет)
            </span>
          </q-checkbox>

          <div v-if="error" class="text-negative text-body2">{{ error }}</div>
          <q-btn type="submit" color="primary" class="full-width" :loading="loading" label="Зарегистрироваться" />
        </q-form>
        <LegalDocDialog v-model="dialogOpen" :slug="dialogSlug" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { api, getToken } from "@/shared/api";
import { useAuthStore } from "@/features/auth/authStore";
import LegalDocDialog from "@/shared/LegalDocDialog.vue";
import TgField from "@/shared/TgField.vue";

const auth = useAuthStore();
const router = useRouter();
const loading = ref(false);
const error = ref("");
const dialogOpen = ref(false);
const dialogSlug = ref("privacy");

const form = reactive({
  full_name: "",
  phone: "",
  email: "",
  birth_date: "",
  programRules: false,
  personalData: false,
  advertising: false,
});

function openDoc(slug: string) {
  dialogSlug.value = slug;
  dialogOpen.value = true;
}

onMounted(async () => {
  if (!getToken()) {
    await auth.authenticate();
  }
});

async function submit() {
  error.value = "";
  if (!form.full_name.trim() || !form.phone.trim() || !form.email.trim() || !form.birth_date) {
    error.value = "Заполните ФИО, телефон, email и дату рождения";
    return;
  }
  if (!form.programRules) {
    error.value = "Нужно открыть и принять правила программы лояльности";
    return;
  }
  if (!form.personalData) {
    error.value = "Нужно дать согласие на обработку персональных данных и ознакомиться с политикой";
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
