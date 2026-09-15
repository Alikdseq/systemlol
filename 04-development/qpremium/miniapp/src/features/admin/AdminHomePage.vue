<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-sm">Админ-панель</div>
    <div class="text-body2 text-grey-7 q-mb-md">
      Выберите раздел. «Касса» — операции как у кассира (с возвратом сюда).
    </div>
    <div class="column q-gutter-sm">
      <q-btn color="primary" text-color="dark" to="/admin/pending" label="Ожидают подтверждения" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/admin/clients" label="Клиенты" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/admin/stores" label="Магазины / кассиры" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/admin/settings" label="Настройки" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/store" label="Режим кассы →" class="full-width" />
      <q-btn
        outline
        color="primary"
        text-color="dark"
        to="/design-preview"
        label="Посмотреть дизайн"
        class="full-width design-preview-btn"
      />
      <div class="text-caption text-grey-7">
        Отдельный превью клиентского интерфейса (Private Fashion Club). Текущий рабочий UI не меняет.
      </div>
    </div>
  </q-page>
</template>
<script setup lang="ts"></script>

<style scoped>
.design-preview-btn {
  margin-top: 8px;
  border-width: 1.5px !important;
  font-weight: 600;
}
</style>
