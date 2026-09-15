<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-md">Настройки программы</div>
    <q-form v-if="form" class="q-gutter-md" @submit.prevent="save">
      <q-input
        v-model="form.accrual_percent"
        type="text"
        label="Процент начисления, %"
        hint="Сколько баллов от суммы покупки (например 5 = 5%)"
        outlined
        stack-label
      />
      <q-input
        v-model="form.max_redeem_percent"
        type="text"
        label="Максимум списания от покупки, %"
        hint="Какую долю чека можно оплатить баллами (например 30)"
        outlined
        stack-label
      />
      <q-input
        v-model="form.min_purchase_amount"
        type="text"
        label="Минимальная сумма покупки для начисления, ₽"
        hint="Ниже этой суммы баллы не начисляются"
        outlined
        stack-label
      />
      <q-input
        v-model="form.earned_ttl_days"
        type="text"
        label="Срок накопительных баллов, дней"
        hint="Через сколько дней сгорают баллы с покупок"
        outlined
        stack-label
      />
      <q-input
        v-model="form.gift_ttl_days"
        type="text"
        label="Срок подарочных баллов, дней"
        hint="Срок жизни подарков и бонусов за регистрацию/ДР"
        outlined
        stack-label
      />
      <q-input
        v-model="form.registration_gift_points"
        type="text"
        label="Подарок за регистрацию, баллов"
        outlined
        stack-label
      />
      <q-input
        v-model="form.birthday_gift_points"
        type="text"
        label="Подарок в день рождения, баллов"
        outlined
        stack-label
      />
      <q-input
        v-model="form.birthday_message_template"
        type="textarea"
        label="Текст поздравления с днём рождения"
        hint="Можно использовать {points} — подставится число баллов"
        outlined
        autogrow
      />
      <q-separator />
      <div class="text-subtitle1">Напоминание о сгорании баллов</div>
      <div class="text-caption text-grey-7">
        Система заранее пишет клиенту в Telegram. Плейсхолдеры: {points}, {days}, {date}.
      </div>
      <q-input
        v-model="form.points_expiry_warning_days"
        type="text"
        label="За сколько дней предупреждать"
        hint="Например 7 — за неделю до сгорания"
        outlined
        stack-label
      />
      <q-input
        v-model="form.points_expiry_warning_template"
        type="textarea"
        label="Текст напоминания о сгорании"
        outlined
        autogrow
      />
      <q-input
        v-model="form.rules_text"
        type="textarea"
        label="Текст правил программы (для клиента)"
        outlined
        autogrow
      />

      <q-separator />
      <div class="text-subtitle1">Приветствие бота (/start)</div>
      <q-input
        v-model="form.bot_welcome_text"
        type="textarea"
        label="Текст приветствия"
        outlined
        autogrow
      />
      <div v-if="form.bot_welcome_photo_url && !clearPhoto" class="q-mb-sm">
        <img
          :src="welcomePhotoSrc"
          alt="Приветствие"
          style="max-width: 100%; max-height: 180px; object-fit: cover; border-radius: 8px"
        />
        <div>
          <q-btn
            flat
            dense
            color="negative"
            text-color="negative"
            label="Убрать фото"
            :loading="photoBusy"
            :disable="busy"
            @click="removeWelcomePhoto"
          />
        </div>
      </div>
      <div v-else-if="clearPhoto" class="text-caption text-grey-7 q-mb-sm">Фото будет удалено после сохранения</div>
      <q-file v-model="photoFile" label="Фото к приветствию (одно)" accept="image/*" outlined dense clearable />

      <q-btn type="submit" color="primary" text-color="dark" :loading="busy" label="Сохранить настройки" />
      <div v-if="msg" class="text-positive">{{ msg }}</div>
      <div v-if="error" class="text-negative">{{ error }}</div>
    </q-form>

    <q-separator class="q-my-lg" />
    <div class="text-subtitle1 q-mb-sm">Акции (карточки)</div>
    <div class="text-caption text-grey-7 q-mb-md">Каждая акция — отдельный блок с условиями, текстом и скидкой (% или ₽).</div>

    <q-card v-for="p in promos" :key="p.id" flat bordered class="q-mb-md">
      <q-card-section class="q-gutter-sm">
        <q-input v-model="p.title" label="Название" outlined stack-label />
        <q-input v-model="p.conditions_text" type="textarea" label="Условия" outlined stack-label autogrow />
        <q-input v-model="p.body_text" type="textarea" label="Текст акции" outlined stack-label autogrow />
        <div class="row q-col-gutter-sm">
          <div class="col-6">
            <q-select
              v-model="p.unit"
              :options="unitOpts"
              label="Ед. изм."
              outlined
              stack-label
              emit-value
              map-options
            />
          </div>
          <div class="col-6">
            <q-input v-model="p.value" type="text" label="Значение" outlined stack-label />
          </div>
        </div>
        <q-toggle v-model="p.is_active" label="Активна" />
        <div class="row q-gutter-sm">
          <q-btn color="primary" text-color="dark" size="sm" label="Сохранить" @click="savePromo(p)" />
          <q-btn color="negative" outline size="sm" label="Удалить" @click="removePromo(p)" />
        </div>
      </q-card-section>
    </q-card>

    <q-card flat bordered class="q-mb-lg bg-grey-1">
      <q-card-section class="q-gutter-sm">
        <div class="text-subtitle2">Новая акция</div>
        <q-input v-model="newPromo.title" label="Название" outlined stack-label />
        <q-input v-model="newPromo.conditions_text" type="textarea" label="Условия" outlined stack-label autogrow />
        <q-input v-model="newPromo.body_text" type="textarea" label="Текст акции" outlined stack-label autogrow />
        <div class="row q-col-gutter-sm">
          <div class="col-6">
            <q-select
              v-model="newPromo.unit"
              :options="unitOpts"
              label="Ед. изм."
              outlined
              stack-label
              emit-value
              map-options
            />
          </div>
          <div class="col-6">
            <q-input v-model="newPromo.value" type="text" label="Значение" outlined stack-label />
          </div>
        </div>
        <q-btn color="primary" text-color="dark" label="Добавить акцию" @click="addPromo" />
      </q-card-section>
    </q-card>

    <q-separator class="q-my-lg" />
    <div class="text-subtitle1 q-mb-sm">Администраторы</div>
    <div class="text-caption text-grey-7 q-mb-md">
      Добавьте коллегу по Telegram ID. Нельзя отключить или удалить последнего активного админа.
    </div>

    <q-card flat bordered class="q-mb-md bg-grey-1">
      <q-card-section class="q-gutter-sm">
        <div class="text-subtitle2">Новый администратор</div>
        <TgField
          v-model="newAdmin.telegram_id"
          label="Telegram ID"
          hint="Только цифры. Узнать ID: бот @userinfobot. Можно вставить копированием."
        />
        <TgField v-model="newAdmin.display_name" label="Имя (необязательно)" />
        <q-btn
          color="primary"
          text-color="dark"
          label="Добавить администратора"
          :loading="addingAdmin"
          :disable="addingAdmin || Boolean(adminActionId)"
          @click="addAdmin"
        />
      </q-card-section>
    </q-card>

    <q-list bordered separator class="q-mb-lg">
      <q-item v-for="a in admins" :key="a.id">
        <q-item-section>
          <q-item-label>{{ a.display_name || "Администратор" }}</q-item-label>
          <q-item-label caption>Telegram ID: {{ a.telegram_id }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="column q-gutter-xs">
            <q-badge :color="a.is_active ? 'positive' : 'grey'" text-color="white">
              {{ a.is_active ? "активен" : "отключён" }}
            </q-badge>
            <q-btn
              v-if="a.is_active"
              size="sm"
              outline
              color="warning"
              label="Отключить"
              :loading="adminActionId === a.id"
              :disable="addingAdmin || Boolean(adminActionId)"
              @click="setAdminActive(a, false)"
            />
            <q-btn
              v-else
              size="sm"
              outline
              color="primary"
              text-color="dark"
              label="Включить"
              :loading="adminActionId === a.id"
              :disable="addingAdmin || Boolean(adminActionId)"
              @click="setAdminActive(a, true)"
            />
            <q-btn
              size="sm"
              outline
              color="negative"
              label="Удалить"
              :loading="adminActionId === a.id + ':del'"
              :disable="addingAdmin || Boolean(adminActionId)"
              @click="removeAdmin(a)"
            />
          </div>
        </q-item-section>
      </q-item>
      <q-item v-if="!admins.length"><q-item-section>Список пуст</q-item-section></q-item>
    </q-list>

    <q-separator class="q-my-lg" />
    <q-btn color="primary" text-color="dark" :loading="backupBusy" label="Скачать резервную копию БД" @click="downloadBackup" />
    <div class="text-caption text-grey-7 q-mt-sm">Файл .dump сохранится на ваш ПК. Можно восстановить PostgreSQL через pg_restore.</div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { api, getToken } from "@/shared/api";
import TgField from "@/shared/TgField.vue";

type SettingsForm = {
  accrual_percent: string;
  max_redeem_percent: string;
  min_purchase_amount: string;
  earned_ttl_days: string | number;
  gift_ttl_days: string | number;
  registration_gift_points: string | number;
  birthday_gift_points: string | number;
  birthday_message_template: string;
  points_expiry_warning_days: string | number;
  points_expiry_warning_template: string;
  rules_text: string;
  bot_welcome_text: string;
  bot_welcome_photo_url?: string;
};

type Promo = {
  id: string;
  title: string;
  conditions_text: string;
  body_text: string;
  unit: string;
  value: string;
  is_active: boolean;
};

type AdminRow = {
  id: string;
  telegram_id: number;
  display_name: string;
  is_active: boolean;
};

const form = ref<SettingsForm | null>(null);
const promos = ref<Promo[]>([]);
const admins = ref<AdminRow[]>([]);
const photoFile = ref<File | null>(null);
const clearPhoto = ref(false);
const busy = ref(false);
const photoBusy = ref(false);
const backupBusy = ref(false);
const addingAdmin = ref(false);
const adminActionId = ref<string | null>(null);
const msg = ref("");
const error = ref("");
const unitOpts = [
  { label: "%", value: "percent" },
  { label: "₽", value: "rub" },
];
const newPromo = reactive({
  title: "",
  conditions_text: "",
  body_text: "",
  unit: "percent",
  value: "10",
});
const newAdmin = reactive({ telegram_id: "", display_name: "" });
const welcomePhotoSrc = computed(() => {
  const url = form.value?.bot_welcome_photo_url || "";
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${window.location.origin}${url.startsWith("/") ? "" : "/"}${url}`;
});

async function load() {
  form.value = await api<SettingsForm>("/api/v1/settings");
  clearPhoto.value = false;
  const p = await api<{ results: Promo[] }>("/api/v1/promotions");
  promos.value = p.results || [];
  const a = await api<{ results: AdminRow[] }>("/api/v1/admins");
  admins.value = a.results || [];
}

async function patchSettings(fd: FormData): Promise<SettingsForm> {
  const token = getToken();
  const res = await fetch("/api/v1/settings", {
    method: "PATCH",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: fd,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw { message: data?.error?.message || "Ошибка сохранения" };
  }
  return (await res.json()) as SettingsForm;
}

async function removeWelcomePhoto() {
  if (!form.value?.bot_welcome_photo_url) return;
  photoBusy.value = true;
  msg.value = "";
  error.value = "";
  try {
    const fd = new FormData();
    fd.append("clear_bot_welcome_photo", "true");
    form.value = await patchSettings(fd);
    clearPhoto.value = false;
    photoFile.value = null;
    msg.value = "Фото убрано";
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Не удалось убрать фото";
  } finally {
    photoBusy.value = false;
  }
}

async function save() {
  if (!form.value) return;
  busy.value = true;
  msg.value = "";
  error.value = "";
  try {
    const fd = new FormData();
    const payload = { ...form.value };
    delete (payload as { bot_welcome_photo_url?: string }).bot_welcome_photo_url;
    for (const [k, v] of Object.entries(payload)) {
      if (v !== undefined && v !== null) fd.append(k, String(v));
    }
    if (photoFile.value) fd.append("bot_welcome_photo", photoFile.value);
    if (clearPhoto.value && !photoFile.value) fd.append("clear_bot_welcome_photo", "true");
    form.value = await patchSettings(fd);
    photoFile.value = null;
    clearPhoto.value = false;
    msg.value = "Сохранено";
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    busy.value = false;
  }
}

async function addPromo() {
  error.value = "";
  try {
    await api("/api/v1/promotions", {
      method: "POST",
      json: { ...newPromo, is_active: true },
    });
    newPromo.title = "";
    newPromo.conditions_text = "";
    newPromo.body_text = "";
    newPromo.value = "10";
    await load();
    msg.value = "Акция добавлена";
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}

async function savePromo(p: Promo) {
  try {
    await api(`/api/v1/promotions/${p.id}`, {
      method: "PATCH",
      json: {
        title: p.title,
        conditions_text: p.conditions_text,
        body_text: p.body_text,
        unit: p.unit,
        value: p.value,
        is_active: p.is_active,
      },
    });
    msg.value = "Акция сохранена";
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}

async function removePromo(p: Promo) {
  if (!confirm(`Удалить акцию «${p.title}»?`)) return;
  try {
    await api(`/api/v1/promotions/${p.id}`, { method: "DELETE" });
    await load();
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  }
}

async function downloadBackup() {
  backupBusy.value = true;
  error.value = "";
  try {
    const token = getToken();
    const res = await fetch("/api/v1/backups/latest/download", {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      error.value = data?.error?.message || "Не удалось скачать резервную копию";
      return;
    }
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const m = /filename="?([^"]+)"?/.exec(cd);
    const filename = m?.[1] || "qpremium_backup.dump";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    msg.value = "Резервная копия скачана";
  } catch {
    error.value = "Ошибка скачивания";
  } finally {
    backupBusy.value = false;
  }
}

async function addAdmin() {
  error.value = "";
  msg.value = "";
  const tid = Number(String(newAdmin.telegram_id).trim());
  if (!tid) {
    error.value = "Укажите Telegram ID";
    return;
  }
  addingAdmin.value = true;
  try {
    await api("/api/v1/admins", {
      method: "POST",
      json: { telegram_id: tid, display_name: newAdmin.display_name.trim() },
    });
    newAdmin.telegram_id = "";
    newAdmin.display_name = "";
    await load();
    msg.value = "Администратор добавлен. Пусть откроет бота командой /start.";
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    addingAdmin.value = false;
  }
}

async function setAdminActive(a: AdminRow, is_active: boolean) {
  error.value = "";
  adminActionId.value = a.id;
  try {
    await api(`/api/v1/admins/${a.id}`, { method: "PATCH", json: { is_active } });
    await load();
    msg.value = is_active ? "Администратор включён" : "Администратор отключён";
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    adminActionId.value = null;
  }
}

async function removeAdmin(a: AdminRow) {
  if (!confirm(`Удалить администратора ${a.display_name || a.telegram_id}?`)) return;
  error.value = "";
  adminActionId.value = `${a.id}:del`;
  try {
    await api(`/api/v1/admins/${a.id}`, { method: "DELETE" });
    await load();
    msg.value = "Администратор удалён";
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message || "Ошибка";
  } finally {
    adminActionId.value = null;
  }
}

onMounted(load);
</script>
