<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <q-page class="q-pa-md flex flex-center">
        <div class="column items-center q-gutter-md" style="max-width: 360px; width: 100%">
          <div class="text-h6">Q Premium</div>
          <q-spinner-dots v-if="auth.state === 'AUTH_LOADING'" color="primary" size="40px" />
          <template v-else>
            <div class="text-body2 text-center text-negative">{{ auth.errorMessage || "Ошибка входа" }}</div>
            <q-btn color="primary" label="Повторить" @click="retry" />
          </template>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/features/auth/authStore";

const auth = useAuthStore();
const router = useRouter();

async function retry() {
  await auth.authenticate();
  if (auth.state === "AUTHENTICATED") {
    await router.replace(auth.homePathForRole());
  }
}

onMounted(retry);

watch(
  () => auth.state,
  async (s) => {
    if (s === "AUTHENTICATED") await router.replace(auth.homePathForRole());
  },
);
</script>
