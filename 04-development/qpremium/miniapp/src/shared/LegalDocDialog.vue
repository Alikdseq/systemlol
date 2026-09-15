<template>
  <q-dialog v-model="open">
    <q-card style="max-width: 720px; width: 100%">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-subtitle1">{{ title }}</div>
        <q-space />
        <q-btn v-close-popup icon="close" flat round dense />
      </q-card-section>
      <q-card-section class="scroll" style="max-height: 70vh; white-space: pre-wrap; font-size: 14px; line-height: 1.45">
        <div v-if="loading">Загрузка…</div>
        <div v-else-if="error" class="text-negative">{{ error }}</div>
        <div v-else>{{ text }}</div>
      </q-card-section>
      <q-card-actions align="right">
        <q-btn v-close-popup flat label="Закрыть" color="primary" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { api } from "@/shared/api";

const props = defineProps<{ modelValue: boolean; slug: string }>();
const emit = defineEmits<{ "update:modelValue": [boolean] }>();

const open = ref(props.modelValue);
const loading = ref(false);
const error = ref("");
const title = ref("");
const text = ref("");

watch(
  () => props.modelValue,
  (v) => {
    open.value = v;
    if (v) load();
  },
);
watch(
  () => props.slug,
  () => {
    if (open.value) load();
  },
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const doc = await api<{ title: string; text: string; version: string }>(`/api/v1/legal/${props.slug}`, {
      auth: false,
    });
    title.value = `${doc.title} (${doc.version})`;
    text.value = doc.text;
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Не удалось загрузить документ";
  } finally {
    loading.value = false;
  }
}
</script>
