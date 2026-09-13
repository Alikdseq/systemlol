<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-dark">
      <q-toolbar>
        <q-toolbar-title shrink class="ellipsis">
          Касса · {{ storeTitle }}
        </q-toolbar-title>
        <q-space />
        <q-btn
          v-if="auth.canUseClientUi"
          flat
          dense
          no-caps
          text-color="dark"
          label="Мой баланс"
          @click="toClient"
        />
        <q-btn
          v-if="auth.role === 'ADMIN'"
          flat
          dense
          no-caps
          text-color="dark"
          label="← Админ"
          to="/admin"
        />
      </q-toolbar>
    </q-header>
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/features/auth/authStore";
import { selectedStoreRef } from "@/shared/storeContext";

const auth = useAuthStore();
const router = useRouter();

const storeTitle = computed(() => {
  return auth.store?.name || selectedStoreRef.value?.name || "магазин";
});

function toClient() {
  auth.setUiMode("client");
  router.push("/");
}
</script>
