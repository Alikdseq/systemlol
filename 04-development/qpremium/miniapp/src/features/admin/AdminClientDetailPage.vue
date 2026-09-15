<template>
  <q-page class="q-pa-md">
    <q-btn flat icon="arrow_back" to="/admin/clients" label="Назад" />
    <div v-if="c" class="q-mt-md">
      <div class="text-h6">{{ c.full_name }}</div>
      <div class="text-body2">{{ c.phone }} · {{ c.email || "email не указан" }}</div>
      <div class="text-caption q-mb-md">
        Дата рождения: {{ c.birth_date }}
        <span v-if="c.registered_at_display"> · Регистрация: {{ c.registered_at_display }}</span>
      </div>

      <div class="q-mb-md">
        <div class="text-subtitle2">Баланс</div>
        <div class="text-body1">Всего: <b>{{ c.balance?.total ?? 0 }}</b> баллов</div>
        <div class="text-body2 text-grey-8">
          Накопительные: {{ c.balance?.earned ?? 0 }} · Подарочные: {{ c.balance?.gift ?? 0 }}
        </div>
      </div>

      <div class="q-mb-md">
        <div class="text-subtitle2 q-mb-sm">Согласия</div>
        <q-list bordered separator dense>
          <q-item v-for="item in c.consents_display || []" :key="item.type">
            <q-item-section>
              <q-item-label>{{ item.label }}</q-item-label>
              <q-item-label caption>{{ item.status_detail }}</q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-badge :color="item.status === 'принято' ? 'positive' : 'grey'">{{ item.status }}</q-badge>
            </q-item-section>
          </q-item>
        </q-list>
      </div>

      <q-separator class="q-my-md" />
      <div class="text-subtitle2">Изменить дату рождения (сразу)</div>
      <div class="row q-col-gutter-sm items-center q-mb-md">
        <div class="col"><q-input v-model="birthEdit" type="date" outlined stack-label label="Дата рождения" /></div>
        <div class="col-auto"><q-btn outline color="primary" label="Сохранить ДР" :loading="busyBirth" @click="saveBirth" /></div>
      </div>

      <div class="text-subtitle2 q-mt-md">Подарочные баллы</div>
      <div class="text-caption text-grey-7 q-mb-sm">Начисляются сразу, без подтверждения. Клиент получит сообщение в Telegram.</div>
      <div class="row q-col-gutter-sm items-center">
        <div class="col">
          <q-input
            v-model="giftPoints"
            type="text"
            outlined
            stack-label
            label="Баллы"
          />
        </div>
        <div class="col-auto"><q-btn color="primary" label="Начислить подарок" :loading="busy" @click="gift" /></div>
      </div>

      <div class="text-subtitle2 q-mt-md">Ручная корректировка</div>
      <div class="text-caption text-grey-7 q-mb-sm">Можно начислить или списать (отрицательное число). Причина обязательна.</div>
      <div class="row q-col-gutter-sm items-center">
        <div class="col-3">
          <q-select
            v-model="adjType"
            :options="adjTypeOpts"
            emit-value
            map-options
            outlined
            stack-label
            label="Тип"
          />
        </div>
        <div class="col-3">
          <q-input v-model="adjPoints" type="text" outlined stack-label label="Баллы (+/−)" />
        </div>
        <div class="col">
          <q-input v-model="adjComment" outlined stack-label label="Причина" />
        </div>
        <div class="col-auto">
          <q-btn outline color="primary" label="Применить" :loading="busyAdj" @click="adjust" />
        </div>
      </div>
      <div v-if="msg" class="text-positive q-mt-sm">{{ msg }}</div>
      <div v-if="error" class="text-negative q-mt-sm">{{ error }}</div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "@/shared/api";

const route = useRoute();
const id = route.params.id as string;
const c = ref<{
  full_name: string;
  phone: string;
  email: string;
  birth_date: string;
  registered_at_display?: string;
  balance?: { total: number; earned: number; gift: number };
  consents_display?: { type: string; label: string; status: string; status_detail: string }[];
} | null>(null);
const giftPoints = ref("100");
const birthEdit = ref("");
const busy = ref(false);
const busyBirth = ref(false);
const busyAdj = ref(false);
const msg = ref("");
const error = ref("");
const adjPoints = ref("-10");
const adjComment = ref("");
const adjType = ref("earned");
const adjTypeOpts = [
  { label: "Накопительные", value: "earned" },
  { label: "Подарочные", value: "gift" },
];

async function load() {
  c.value = await api(`/api/v1/clients/${id}`);
  birthEdit.value = c.value?.birth_date || "";
}

async function gift() {
  busy.value = true;
  msg.value = "";
  error.value = "";
  try {
    await api(`/api/v1/clients/${id}/gifts`, {
      method: "POST",
      json: { points: Number(giftPoints.value), comment: "Подарок от администратора" },
    });
    msg.value = "Подарок начислен, клиенту отправлено сообщение";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = false;
  }
}

async function adjust() {
  busyAdj.value = true;
  msg.value = "";
  error.value = "";
  try {
    const points = Number(adjPoints.value);
    if (!points || Number.isNaN(points)) throw { message: "Укажите число баллов" };
    if (!adjComment.value.trim()) throw { message: "Укажите причину" };
    await api(`/api/v1/clients/${id}/adjustments`, {
      method: "POST",
      json: { points, point_type: adjType.value, comment: adjComment.value.trim() },
    });
    msg.value = "Корректировка применена";
    adjComment.value = "";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busyAdj.value = false;
  }
}

async function saveBirth() {
  busyBirth.value = true;
  msg.value = "";
  error.value = "";
  try {
    await api(`/api/v1/clients/${id}`, {
      method: "PATCH",
      json: { birth_date: birthEdit.value },
    });
    msg.value = "Дата рождения обновлена";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busyBirth.value = false;
  }
}

onMounted(load);
</script>
