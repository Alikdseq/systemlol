<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-dark">
      <q-toolbar>
        <q-toolbar-title>Админ · Q Premium</q-toolbar-title>
        <q-btn
          v-if="auth.canUseClientUi"
          flat
          dense
          no-caps
          text-color="dark"
          label="Мой баланс"
          @click="toClient"
        />
        <q-btn flat dense no-caps text-color="dark" label="Касса →" to="/store" />
      </q-toolbar>
      <q-tabs dense align="left" class="bg-primary text-dark" active-color="dark" outside-arrows mobile-arrows>
        <q-route-tab to="/admin" label="Главная" exact />
        <q-route-tab to="/admin/pending" label="Ожидают" />
        <q-route-tab to="/admin/clients" label="Клиенты" />
        <q-route-tab to="/admin/operations" label="Операции" />
        <q-route-tab to="/admin/stores" label="Магазины" />
        <q-route-tab to="/admin/stats" label="Статистика" />
        <q-route-tab to="/admin/broadcasts" label="Рассылки" />
        <q-route-tab to="/admin/settings" label="Настройки" />
      </q-tabs>
    </q-header>
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/features/auth/authStore";

const auth = useAuthStore();
const router = useRouter();

function toClient() {
  auth.setUiMode("client");
  router.push("/");
}
</script>
