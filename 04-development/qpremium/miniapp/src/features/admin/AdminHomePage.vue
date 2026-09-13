<template>
  <q-page class="q-pa-md">
    <div class="text-h6 q-mb-sm">Админ-панель</div>
    <div class="text-body2 text-grey-7 q-mb-md">Выберите раздел. «Касса» — операции как у кассира (с возвратом сюда).</div>
    <div class="column q-gutter-sm">
      <q-btn color="primary" text-color="dark" to="/admin/pending" label="Ожидают подтверждения" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/admin/clients" label="Клиенты" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/admin/stores" label="Магазины / кассиры" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/admin/settings" label="Настройки" class="full-width" />
      <q-btn color="primary" text-color="dark" to="/store" label="Режим кассы →" class="full-width" />
    </div>
  </q-page>
</template>
<script setup lang="ts"></script>
