<template>
  <q-page class="q-pa-md">
    <div class="row items-center q-mb-md">
      <div class="text-h6 col">Ожидают подтверждения</div>
      <q-btn flat icon="refresh" @click="load" />
    </div>
    <q-banner v-if="error" class="bg-red-1 text-negative q-mb-md" rounded>{{ error }}</q-banner>

    <div class="text-subtitle1 q-mb-sm">Начисления баллов</div>
    <q-list bordered separator class="q-mb-lg">
      <q-item v-for="op in items" :key="op.id" class="q-py-md">
        <q-item-section>
          <q-item-label>{{ op.points }} б. · {{ op.purchase_amount }} ₽</q-item-label>
          <q-item-label caption>
            {{ op.store_name_snapshot }}
            <template v-if="op.operator_name_snapshot"> · Кассир: {{ op.operator_name_snapshot }}</template>
            · {{ op.created_at_display || op.created_at }}
          </q-item-label>
          <div class="row q-col-gutter-xs q-mt-sm items-center">
            <div class="col">
              <q-input
                v-model="edits[op.id]"
                outlined
                stack-label
                type="text"
                label="Новая сумма → пересчёт"
              />
            </div>
            <div class="col-auto">
              <q-btn
                size="sm"
                outline
                color="primary"
                label="Пересчитать"
                :loading="busy === op.id + 'p'"
                @click="patchAmount(op.id)"
              />
            </div>
          </div>
          <div class="row q-col-gutter-xs q-mt-sm items-center">
            <div class="col-4">
              <q-input
                v-model="manualPoints[op.id]"
                outlined
                stack-label
                type="text"
                label="Ручные баллы"
              />
            </div>
            <div class="col">
              <q-input
                v-model="overrideReasons[op.id]"
                outlined
                stack-label
                type="text"
                label="Причина (обязательно)"
              />
            </div>
            <div class="col-auto">
              <q-btn
                size="sm"
                outline
                color="secondary"
                label="Задать баллы"
                :loading="busy === op.id + 'm'"
                @click="patchPoints(op.id)"
              />
            </div>
          </div>
        </q-item-section>
        <q-item-section side top>
          <div class="column q-gutter-xs">
            <q-btn size="sm" color="positive" label="OK" :loading="busy === op.id + 'c'" @click="confirm(op.id)" />
            <q-btn size="sm" color="negative" outline label="Откл." :loading="busy === op.id + 'r'" @click="reject(op.id)" />
          </div>
        </q-item-section>
      </q-item>
      <q-item v-if="!items.length"><q-item-section>Нет начислений в ожидании</q-item-section></q-item>
    </q-list>

    <div class="text-subtitle1 q-mb-sm">Смена даты рождения</div>
    <q-list bordered separator>
      <q-item v-for="r in birthRequests" :key="r.id" class="q-py-md">
        <q-item-section>
          <q-item-label>{{ r.client_name }} · {{ r.client_phone }}</q-item-label>
          <q-item-label caption>
            {{ r.old_value }} → {{ r.new_value }} · {{ r.created_at_display || r.created_at }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="column q-gutter-xs">
            <q-btn size="sm" color="positive" label="OK" :loading="busy === r.id + 'a'" @click="decideBirth(r.id, 'approve')" />
            <q-btn size="sm" color="negative" outline label="Откл." :loading="busy === r.id + 'x'" @click="decideBirth(r.id, 'reject')" />
          </div>
        </q-item-section>
      </q-item>
      <q-item v-if="!birthRequests.length"><q-item-section>Нет запросов на смену ДР</q-item-section></q-item>
    </q-list>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { api } from "@/shared/api";

type Op = {
  id: string;
  points: number;
  purchase_amount: string | null;
  store_name_snapshot: string;
  operator_name_snapshot?: string;
  created_at: string;
  created_at_display?: string;
};

type BirthReq = {
  id: string;
  client_name: string;
  client_phone: string;
  old_value: string;
  new_value: string;
  created_at: string;
  created_at_display?: string;
};

const items = ref<Op[]>([]);
const birthRequests = ref<BirthReq[]>([]);
const error = ref("");
const busy = ref("");
const edits = reactive<Record<string, string>>({});
const manualPoints = reactive<Record<string, string>>({});
const overrideReasons = reactive<Record<string, string>>({});

async function load() {
  error.value = "";
  try {
    const [data, births] = await Promise.all([
      api<{ results: Op[] }>("/api/v1/operations/pending"),
      api<{ results: BirthReq[] }>("/api/v1/profile-changes/pending"),
    ]);
    items.value = data.results || [];
    birthRequests.value = births.results || [];
    for (const op of items.value) {
      if (edits[op.id] === undefined) edits[op.id] = op.purchase_amount || "";
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}

async function patchAmount(id: string) {
  busy.value = id + "p";
  error.value = "";
  try {
    await api(`/api/v1/operations/${id}`, {
      method: "PATCH",
      json: { purchase_amount: String(edits[id] || "").replace(",", ".") },
    });
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка правки";
  } finally {
    busy.value = "";
  }
}

async function patchPoints(id: string) {
  busy.value = id + "m";
  error.value = "";
  try {
    const points = Number(manualPoints[id]);
    const reason = String(overrideReasons[id] || "").trim();
    if (!points || points <= 0) throw { message: "Укажите баллы > 0" };
    if (!reason) throw { message: "Укажите причину ручного изменения" };
    await api(`/api/v1/operations/${id}`, {
      method: "PATCH",
      json: { points, override_reason: reason },
    });
    manualPoints[id] = "";
    overrideReasons[id] = "";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка правки баллов";
  } finally {
    busy.value = "";
  }
}

async function confirm(id: string) {
  busy.value = id + "c";
  try {
    await api(`/api/v1/operations/${id}/confirm`, { method: "POST", json: {} });
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = "";
  }
}

async function reject(id: string) {
  busy.value = id + "r";
  try {
    await api(`/api/v1/operations/${id}/reject`, { method: "POST", json: { reason: "" } });
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = "";
  }
}

async function decideBirth(id: string, action: "approve" | "reject") {
  busy.value = id + (action === "approve" ? "a" : "x");
  try {
    await api(`/api/v1/profile-changes/${id}/decide`, {
      method: "POST",
      json: { action },
    });
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = "";
  }
}

onMounted(load);
</script>
