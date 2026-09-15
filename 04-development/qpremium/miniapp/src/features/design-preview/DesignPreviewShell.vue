<template>
  <div class="qp-design">
    <div class="qp-design__bg" aria-hidden="true" />
    <div class="qp-design__shell">
      <header class="qp-design__top">
        <button type="button" class="qp-design__exit" @click="leave">← Админ</button>
        <div class="qp-design__brand">
          <span class="qp-design__brand-mark">Q PREMIUM</span>
          <span class="qp-design__brand-sub">Private Fashion Club</span>
        </div>
      </header>

      <main class="qp-design__scroll">
        <router-view />
      </main>

      <nav class="qp-design__nav" aria-label="Разделы">
        <button
          v-for="item in tabs"
          :key="item.to"
          type="button"
          class="qp-design__nav-item"
          :class="{ 'is-active': route.path.startsWith(item.to) }"
          @click="router.push(item.to)"
        >
          <span class="qp-design__nav-ico" aria-hidden="true">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { loadDesignDemo } from "./useDesignDemo";
import "./design-theme.css";

const route = useRoute();
const router = useRouter();

const tabs = [
  { to: "/design-preview/balance", label: "Баланс", icon: "◇" },
  { to: "/design-preview/promos", label: "Акции", icon: "%" },
  { to: "/design-preview/rules", label: "Правила", icon: "≡" },
  { to: "/design-preview/data", label: "Данные", icon: "◎" },
];

function leave() {
  router.push("/admin");
}

onMounted(() => {
  loadDesignDemo(true);
});
</script>
