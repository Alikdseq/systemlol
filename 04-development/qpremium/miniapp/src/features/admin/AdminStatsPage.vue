<template>
  <q-page class="q-pa-md stats-page">
    <div class="text-h6 q-mb-md">Статистика</div>

    <div class="period-grid q-mb-md">
      <q-btn
        v-for="o in opts"
        :key="o.value"
        :outline="period !== o.value"
        :unelevated="period === o.value"
        :color="period === o.value ? 'primary' : 'grey-7'"
        :label="o.label"
        no-caps
        class="period-btn"
        @click="selectPeriod(o.value)"
      />
    </div>

    <div v-if="period === 'custom'" class="column q-gutter-sm q-mb-md">
      <q-input v-model="dateFrom" type="date" outlined stack-label label="С даты" />
      <q-input v-model="dateTo" type="date" outlined stack-label label="По дату" />
      <q-btn color="primary" class="full-width" label="Показать" :loading="loading" @click="load" />
    </div>

    <q-banner v-if="error" class="bg-red-1 text-negative q-mb-md" rounded>{{ error }}</q-banner>

    <div v-if="data" class="table-wrap q-mb-lg">
      <q-markup-table flat bordered dense>
        <thead>
          <tr>
            <th class="text-left">Показатель</th>
            <th class="text-right">Значение</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>Клиентов всего</td><td class="text-right">{{ data.clients_total }}</td></tr>
          <tr><td>Новых клиентов за период</td><td class="text-right">{{ data.clients_new }}</td></tr>
          <tr><td>Начислений (подтверждённых)</td><td class="text-right">{{ data.accruals_count }}</td></tr>
          <tr><td>Начислено баллов</td><td class="text-right">{{ data.accruals_points }}</td></tr>
          <tr><td>Сумма покупок по начислениям</td><td class="text-right">{{ data.accruals_purchase_sum }} ₽</td></tr>
          <tr><td>Списаний</td><td class="text-right">{{ data.redemptions_count }}</td></tr>
          <tr><td>Списано баллов</td><td class="text-right">{{ data.redemptions_points }}</td></tr>
          <tr><td>Ждут подтверждения сейчас</td><td class="text-right">{{ data.pending_count }}</td></tr>
        </tbody>
      </q-markup-table>
    </div>

    <div class="text-subtitle2 q-mb-sm" v-if="data">По магазинам (начисления)</div>
    <div v-if="data" class="table-wrap">
      <q-markup-table flat bordered dense>
        <thead>
          <tr>
            <th class="text-left">Магазин</th>
            <th class="text-right">Оп.</th>
            <th class="text-right">Баллы</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in data.by_store || []" :key="i">
            <td class="store-cell">{{ row.store_name_snapshot || "—" }}</td>
            <td class="text-right">{{ row.count }}</td>
            <td class="text-right">{{ row.points }}</td>
          </tr>
          <tr v-if="!(data.by_store || []).length">
            <td colspan="3">Нет данных за период</td>
          </tr>
        </tbody>
      </q-markup-table>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api } from "@/shared/api";

type Stats = {
  clients_total: number;
  clients_new: number;
  accruals_count: number;
  accruals_points: number;
  accruals_purchase_sum: string;
  redemptions_count: number;
  redemptions_points: number;
  pending_count: number;
  by_store: { store_name_snapshot: string; count: number; points: number }[];
};

const period = ref("month");
const dateFrom = ref("");
const dateTo = ref("");
const opts = [
  { label: "Неделя", value: "week" },
  { label: "Месяц", value: "month" },
  { label: "Год", value: "year" },
  { label: "Свои даты", value: "custom" },
];
const data = ref<Stats | null>(null);
const error = ref("");
const loading = ref(false);

function selectPeriod(value: string) {
  period.value = value;
  if (value !== "custom") load();
}

async function load() {
  error.value = "";
  loading.value = true;
  try {
    let url = `/api/v1/statistics?period=${period.value}`;
    if (period.value === "custom") {
      if (!dateFrom.value || !dateTo.value) {
        error.value = "Укажите даты «с» и «по»";
        data.value = null;
        return;
      }
      url += `&from=${dateFrom.value}&to=${dateTo.value}`;
    }
    data.value = await api<Stats>(url);
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    loading.value = false;
  }
}
onMounted(load);
</script>

<style scoped>
.stats-page {
  max-width: 100%;
  overflow-x: hidden;
}

.period-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  width: 100%;
}

.period-btn {
  width: 100%;
  min-height: 40px;
}

.table-wrap {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.store-cell {
  word-break: break-word;
  max-width: 55vw;
}
</style>
