<template>
  <div class="qp-fade promos">
    <div class="qp-kicker">Актуальные предложения</div>
    <h1 class="qp-title">Акции<br />Q Premium</h1>
    <p class="qp-lead">Специальные условия, подарки и привилегии только для вас.</p>

    <div v-if="items.length" class="promos__list">
      <article
        v-for="(p, idx) in items"
        :key="p.id"
        class="promos__card"
        :class="`promos__card--${idx % 3}`"
      >
        <div class="promos__num">{{ String(idx + 1).padStart(2, "0") }}</div>
        <div v-if="p.badge" class="promos__value" aria-label="Значение акции">{{ p.badge }}</div>
        <h2 class="promos__name">{{ p.title }}</h2>
        <p class="promos__body">{{ p.body }}</p>
        <div v-if="p.meta" class="promos__meta">{{ p.meta }}</div>
      </article>
    </div>

    <div v-else class="promos__empty qp-card">
      Следите за новыми предложениями. Мы регулярно обновляем акции для вас.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useDesignDemo } from "./useDesignDemo";

const demo = useDesignDemo();

const items = computed(() => {
  if (demo.promos.length) {
    return demo.promos.map((p) => {
      const n = Number(p.value);
      const badge =
        p.unit === "percent" && Number.isFinite(n)
          ? `+${n} %`
          : Number.isFinite(n) && n > 0
            ? `+${n} ₽`
            : "";
      return {
        id: p.id,
        title: p.title,
        body: p.body_text || p.conditions_text || "Специальное предложение Q Premium",
        meta: p.conditions_text && p.body_text ? p.conditions_text : "",
        badge,
      };
    });
  }
  if (demo.promotionsText.trim()) {
    return [
      {
        id: "legacy",
        title: "Актуальное",
        body: demo.promotionsText,
        meta: "",
        badge: "",
      },
    ];
  }
  return [];
});
</script>

<style scoped>
.promos__list {
  margin-top: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.promos__card {
  position: relative;
  min-height: 190px;
  padding: 22px 20px;
  border-radius: var(--qp-radius);
  overflow: hidden;
  color: var(--qp-ink);
  box-shadow: 0 14px 36px rgba(57, 37, 45, 0.08);
  animation: qpFadeUp 0.75s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.promos__card--0 {
  background:
    linear-gradient(160deg, rgba(248, 246, 243, 0.82), rgba(232, 218, 218, 0.55)),
    url("/app/design/bg-silk.png") center/cover;
}

.promos__card--1 {
  color: #f7f1ea;
  background:
    linear-gradient(160deg, rgba(28, 22, 24, 0.82), rgba(57, 37, 45, 0.55)),
    url("/app/design/bg-dark.png") center/cover;
}

.promos__card--2 {
  background:
    linear-gradient(160deg, rgba(255, 252, 249, 0.88), rgba(197, 143, 157, 0.22)),
    url("/app/design/bg-rose.png") center/cover;
}

.promos__num {
  font-family: var(--qp-serif);
  font-size: 2rem;
  font-weight: 600;
  opacity: 0.35;
  line-height: 1;
}

.promos__value {
  position: absolute;
  top: 16px;
  right: 14px;
  max-width: 58%;
  padding: 10px 14px;
  border-radius: 16px;
  background: rgba(23, 21, 23, 0.9);
  color: #fffaf7;
  font-family: var(--qp-serif);
  font-size: clamp(1.55rem, 7vw, 2.05rem);
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1;
  text-align: center;
  box-shadow: 0 8px 24px rgba(57, 37, 45, 0.22);
  border: 1px solid rgba(180, 154, 106, 0.45);
}

.promos__card--1 .promos__value {
  background: rgba(197, 143, 157, 0.96);
  color: #1c1618;
  border-color: rgba(255, 255, 255, 0.35);
}

.promos__card--2 .promos__value {
  background: linear-gradient(145deg, #c58f9d, #a86f80);
  color: #fffaf7;
  border-color: rgba(255, 255, 255, 0.35);
}

.promos__name {
  margin: 18px 0 0;
  padding-right: 36%;
  font-family: var(--qp-serif);
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  line-height: 1.15;
}

.promos__body {
  margin: 10px 0 0;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.5;
  max-width: 36ch;
  white-space: pre-wrap;
  opacity: 0.9;
}

.promos__meta {
  margin-top: 16px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
  opacity: 0.72;
}

.promos__empty {
  margin-top: 22px;
  padding: 22px 18px;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.5;
  color: var(--qp-ink-soft);
}

.promos__card:nth-child(1) {
  animation-delay: 0.05s;
}
.promos__card:nth-child(2) {
  animation-delay: 0.12s;
}
.promos__card:nth-child(3) {
  animation-delay: 0.2s;
}
</style>
