<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Акции</div>
    <div v-if="!promos.length && !legacy" class="text-body2 text-grey-7">Акций пока нет.</div>
    <div v-if="legacy && !promos.length" class="text-body1" style="white-space: pre-wrap">{{ legacy }}</div>

    <div class="q-gutter-md">
      <q-card v-for="p in promos" :key="p.id" flat bordered class="promo-card">
        <q-card-section>
          <div class="row items-start justify-between">
            <div class="text-h6">{{ p.title }}</div>
            <div class="text-h5 text-weight-bold text-primary">
              {{ formatValue(p) }}
            </div>
          </div>
          <div v-if="p.conditions_text" class="text-caption text-grey-8 q-mt-sm">
            Условия: {{ p.conditions_text }}
          </div>
          <div v-if="p.body_text" class="text-body2 q-mt-sm" style="white-space: pre-wrap">
            {{ p.body_text }}
          </div>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/shared/api";

type Promo = {
  id: string;
  title: string;
  conditions_text: string;
  body_text: string;
  unit: string;
  unit_label: string;
  value: string;
};

const promos = ref<Promo[]>([]);
const legacy = ref("");

function formatValue(p: Promo) {
  const n = Number(p.value);
  if (p.unit === "percent") return `${n} %`;
  return `${n} ₽`;
}

onMounted(async () => {
  const s = await api<{ promotions_text: string; promotions?: Promo[] }>("/api/v1/settings/public");
  promos.value = s.promotions || [];
  legacy.value = s.promotions_text || "";
});
</script>

<style scoped>
.promo-card {
  background: linear-gradient(135deg, #fff5fa 0%, #ffffff 55%);
  border-left: 4px solid #f7bbdd;
}
</style>
