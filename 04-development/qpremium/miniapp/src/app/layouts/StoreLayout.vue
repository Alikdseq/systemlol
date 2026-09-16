<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-dark">
      <q-toolbar class="store-toolbar">
        <q-toolbar-title class="store-toolbar__title">
          <div class="ellipsis">Касса · {{ storeName }}</div>
          <div v-if="storeAddress" class="store-toolbar__addr ellipsis">{{ storeAddress }}</div>
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
import { storeAddressCaption } from "@/shared/dates";

const auth = useAuthStore();
const router = useRouter();

const storeName = computed(() => {
  return auth.store?.name || selectedStoreRef.value?.name || "магазин";
});

const storeAddress = computed(() => {
  const addr = auth.store?.address || selectedStoreRef.value?.address || "";
  if (!addr && !auth.store && !selectedStoreRef.value) return "";
  return storeAddressCaption(addr);
});

function toClient() {
  auth.setUiMode("client");
  router.push("/");
}
</script>
