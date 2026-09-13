<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Рассылки</div>
    <q-banner class="bg-blue-1 q-mb-md" rounded>
      Сообщение получат только клиенты, которые согласились на рекламные сообщения.
    </q-banner>
    <q-input v-model="body" type="textarea" outlined autogrow label="Текст сообщения" class="q-mb-md" />
    <q-btn color="primary" :loading="busy" label="Отправить" @click="send" />
    <div v-if="msg" class="text-positive q-mt-sm">{{ msg }}</div>
    <div v-if="error" class="text-negative q-mt-sm">{{ error }}</div>
    <q-list bordered separator class="q-mt-lg">
      <q-item v-for="b in items" :key="b.id">
        <q-item-section>
          <q-item-label>{{ b.body }}</q-item-label>
          <q-item-label caption>
            Аудитория: {{ b.audience_count }} · Доставлено: {{ b.sent_count }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-page>
</template>
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/shared/api";
const body = ref("");
const busy = ref(false);
const msg = ref("");
const error = ref("");
const items = ref<{ id: string; body: string; audience_count: number; sent_count: number }[]>([]);
async function load() {
  const data = await api<{ results: typeof items.value }>("/api/v1/broadcasts");
  items.value = data.results || [];
}
async function send() {
  busy.value = true;
  msg.value = "";
  error.value = "";
  try {
    const r = await api<{ audience_count: number }>("/api/v1/broadcasts", {
      method: "POST",
      json: { body: body.value },
    });
    msg.value = `В очереди. Получат ${r.audience_count} клиентов с согласием на рекламу.`;
    body.value = "";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = false;
  }
}
onMounted(load);
</script>
