<template>
  <div class="tg-field">
    <label class="tg-field__label" :for="fid">{{ label }}</label>
    <input
      :id="fid"
      class="tg-field__control"
      :value="modelValue"
      :type="type"
      :autocomplete="autocomplete"
      :name="fid"
      :max="max || undefined"
      :min="min || undefined"
      enterkeyhint="next"
      @input="onInput"
    />
    <div v-if="hint" class="tg-field__hint">{{ hint }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    label: string;
    hint?: string;
    type?: "text" | "date";
    autocomplete?: string;
    max?: string;
    min?: string;
  }>(),
  { type: "text", autocomplete: "off" },
);

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const fid = computed(() => {
  const raw = `${props.label}-${props.type}`;
  return `tgf-${raw.replace(/[^a-zA-Z0-9а-яА-Я]+/g, "-").toLowerCase()}`;
});

function onInput(e: Event) {
  emit("update:modelValue", (e.target as HTMLInputElement).value);
}
</script>
