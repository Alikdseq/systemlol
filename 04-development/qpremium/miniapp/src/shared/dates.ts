/** Max selectable birth date = today (local calendar). */
export function maxBirthDateIso(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function isFutureBirthDate(iso: string): boolean {
  const v = (iso || "").trim().slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return false;
  return v > maxBirthDateIso();
}

export function storeAddressCaption(address?: string | null): string {
  const a = (address || "").trim();
  return a || "Адрес не указан";
}
