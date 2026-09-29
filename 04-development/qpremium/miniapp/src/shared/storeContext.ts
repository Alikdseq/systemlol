/** ADMIN в режиме кассы обязан выбрать store_id. */

import { ref } from "vue";

const KEY = "qp_selected_store";

export type SelectedStore = { id: string; name: string; address?: string };

export const selectedStoreRef = ref<SelectedStore | null>(read());

function read(): SelectedStore | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SelectedStore;
  } catch {
    return null;
  }
}

export function getSelectedStore(): SelectedStore | null {
  return selectedStoreRef.value || read();
}

export function setSelectedStore(store: SelectedStore | null): void {
  if (!store) sessionStorage.removeItem(KEY);
  else sessionStorage.setItem(KEY, JSON.stringify(store));
  selectedStoreRef.value = store;
}

/** Для ADMIN — store_id из выбора; для STORE — не передаём (берёт backend из actor). */
export function storeIdForWrite(role: string): string | undefined {
  if (role !== "ADMIN") return undefined;
  return getSelectedStore()?.id;
}
