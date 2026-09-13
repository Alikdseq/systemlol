<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Магазины и кассиры</div>

    <div class="text-subtitle1 q-mb-sm">Магазины</div>
    <q-list bordered separator class="q-mb-md">
      <q-expansion-item
        v-for="s in stores"
        :key="s.id"
        :label="s.name"
        :caption="s.address || 'Адрес не указан'"
      >
        <div class="q-pa-md q-gutter-sm">
          <q-input v-model="s.name" label="Название" outlined stack-label />
          <q-input v-model="s.address" label="Адрес" outlined stack-label />
          <div class="row q-gutter-sm">
            <q-btn color="primary" label="Сохранить магазин" :loading="busy === s.id" @click="saveStore(s)" />
            <q-btn
              color="negative"
              outline
              label="Удалить магазин"
              :loading="busy === s.id + 'd'"
              @click="deleteStore(s)"
            />
          </div>
        </div>
      </q-expansion-item>
      <q-item v-if="!stores.length"><q-item-section>Магазинов пока нет</q-item-section></q-item>
    </q-list>

    <div class="text-subtitle1 q-mb-sm">Добавить магазин</div>
    <div class="row q-col-gutter-sm q-mb-lg">
      <div class="col-12 col-sm-5"><q-input v-model="newName" label="Название" outlined stack-label /></div>
      <div class="col-12 col-sm-5"><q-input v-model="newAddress" label="Адрес" outlined stack-label /></div>
      <div class="col-12 col-sm-2"><q-btn color="primary" class="full-width" label="Добавить" @click="createStore" /></div>
    </div>

    <div class="text-subtitle1 q-mb-sm">Кассиры</div>
    <div class="text-caption text-grey-7 q-mb-sm">
      Привязка по телефону. Кассир сначала регистрируется в программе (как клиент), затем вы привязываете его номер к магазину.
      Администратора сделать кассиром нельзя.
    </div>
    <q-list bordered separator dense class="q-mb-md">
      <q-item v-for="a in accesses" :key="a.id">
        <q-item-section>
          <q-item-label>
            {{ a.full_name || "Кассир" }} · {{ a.phone || "телефон не найден" }} → {{ a.store_name }}
          </q-item-label>
          <q-item-label caption>{{ a.is_active ? "активен" : "отключён" }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-btn
            flat
            dense
            :label="a.is_active ? 'Отключить' : 'Включить'"
            @click="toggleAccess(a)"
          />
        </q-item-section>
      </q-item>
      <q-item v-if="!accesses.length"><q-item-section>Кассиров пока нет</q-item-section></q-item>
    </q-list>

    <div class="row q-col-gutter-sm">
      <div class="col-12 col-sm-5">
        <q-select v-model="storeId" :options="storeOpts" dense outlined label="Магазин" emit-value map-options />
      </div>
      <div class="col-12 col-sm-4">
        <q-input v-model="phone" outlined stack-label type="text" inputmode="tel" label="Телефон кассира" />
      </div>
      <div class="col-12 col-sm-3">
        <q-btn color="primary" text-color="dark" class="full-width" label="Привязать" @click="addAccess" />
      </div>
    </div>

    <div v-if="msg" class="text-positive q-mt-sm">{{ msg }}</div>
    <div v-if="error" class="text-negative q-mt-sm">{{ error }}</div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "@/shared/api";

type Store = { id: string; name: string; address: string; is_active: boolean };
type Access = {
  id: string;
  store_id: string;
  store_name: string;
  phone?: string;
  full_name?: string;
  is_active: boolean;
};

const stores = ref<Store[]>([]);
const accesses = ref<Access[]>([]);
const storeId = ref("");
const phone = ref("");
const newName = ref("");
const newAddress = ref("");
const msg = ref("");
const error = ref("");
const busy = ref("");

const storeOpts = computed(() =>
  stores.value.map((s) => ({ label: s.name, value: s.id })),
);

async function load() {
  const [s, a] = await Promise.all([
    api<{ results: Store[] }>("/api/v1/stores"),
    api<{ results: Access[] }>("/api/v1/store-accesses"),
  ]);
  stores.value = (s.results || []).filter((x) => x.is_active !== false);
  accesses.value = a.results || [];
  if (!storeId.value && storeOpts.value[0]) storeId.value = storeOpts.value[0].value;
}

async function createStore() {
  msg.value = "";
  error.value = "";
  try {
    await api("/api/v1/stores", {
      method: "POST",
      json: { name: newName.value.trim(), address: newAddress.value.trim() },
    });
    newName.value = "";
    newAddress.value = "";
    msg.value = "Магазин добавлен";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}

async function saveStore(s: Store) {
  busy.value = s.id;
  msg.value = "";
  error.value = "";
  try {
    await api(`/api/v1/stores/${s.id}`, {
      method: "PATCH",
      json: { name: s.name, address: s.address },
    });
    msg.value = "Магазин сохранён";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = "";
  }
}

async function deleteStore(s: Store) {
  if (
    !confirm(
      `Удалить магазин «${s.name}» полностью? Он исчезнет из списка. История прошлых операций сохранится (название магазина в снимке). Кассиры этого магазина будут сняты.`,
    )
  ) {
    return;
  }
  busy.value = s.id + "d";
  msg.value = "";
  error.value = "";
  try {
    await api(`/api/v1/stores/${s.id}`, { method: "DELETE" });
    msg.value = "Магазин удалён";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = "";
  }
}

async function addAccess() {
  msg.value = "";
  error.value = "";
  try {
    await api("/api/v1/store-accesses", {
      method: "POST",
      json: { store_id: storeId.value, phone: phone.value.trim() },
    });
    msg.value = "Кассир привязан";
    phone.value = "";
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}

async function toggleAccess(a: Access) {
  error.value = "";
  try {
    await api(`/api/v1/store-accesses/${a.id}`, {
      method: "PATCH",
      json: { is_active: !a.is_active },
    });
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}

onMounted(load);
</script>
