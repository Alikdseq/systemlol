<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Клиенты</div>
    <q-input v-model="q" outlined stack-label label="Поиск ФИО" class="q-mb-md" @keyup.enter="load">
      <template #append><q-btn flat icon="search" @click="load" /></template>
    </q-input>
    <q-btn class="q-mb-md" color="primary" text-color="dark" label="Скачать в Excel" @click="exportXlsx" />
    <q-list bordered separator>
      <q-item v-for="c in items" :key="c.id" clickable :to="`/admin/clients/${c.id}`">
        <q-item-section>
          <q-item-label>{{ c.full_name }}</q-item-label>
          <q-item-label caption>{{ c.phone }} · баланс {{ c.balance_total }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, getToken } from "@/shared/api";

type Row = { id: string; full_name: string; phone: string; balance_total: number };
const q = ref("");
const items = ref<Row[]>([]);

async function load() {
  const data = await api<{ results: Row[] }>(`/api/v1/clients?q=${encodeURIComponent(q.value)}&field=name`);
  items.value = data.results || [];
}

async function exportXlsx() {
  const token = getToken();
  const res = await fetch("/api/v1/clients/export", {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "clients_export.xlsx";
  a.click();
  URL.revokeObjectURL(url);
}

onMounted(load);
</script>
