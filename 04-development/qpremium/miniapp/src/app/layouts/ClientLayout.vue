<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary text-dark">
      <q-toolbar>
        <q-toolbar-title>Q Premium</q-toolbar-title>
        <q-btn
          v-if="auth.canUseWorkUi"
          flat
          dense
          no-caps
          text-color="dark"
          :label="auth.role === 'ADMIN' ? 'В админку →' : 'На кассу →'"
          @click="toWork"
        />
      </q-toolbar>
      <q-tabs dense align="justify" class="bg-primary text-dark" active-color="dark">
        <q-route-tab to="/" label="Баланс" />
        <q-route-tab to="/profile" label="Профиль" />
        <q-route-tab to="/rules" label="Правила" />
        <q-route-tab to="/promos" label="Акции" />
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

function toWork() {
  auth.setUiMode("work");
  router.push(auth.role === "ADMIN" ? "/admin" : "/store");
}
</script>
