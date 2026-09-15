<template>
  <div class="qp-fade bal">
    <div class="qp-kicker">Добро пожаловать{{ demo.firstName ? "," : "" }}</div>
    <h1 class="qp-title">{{ demo.firstName || "Q Premium" }}</h1>
    <p class="qp-lead">Ваши привилегии — наша забота</p>

    <section class="bal__hero qp-card" aria-label="Общий баланс">
      <div class="bal__hero-label">Мои баллы</div>
      <div class="bal__hero-value">{{ formatPoints(demo.total) }}</div>
      <div class="bal__hero-unit">баллов</div>
      <div class="bal__hero-eq">≈ {{ formatPoints(demo.total) }} ₽</div>
      <div class="bal__hero-badge">Premium Member</div>
    </section>

    <section class="bal__block qp-card qp-card--rose">
      <header class="bal__block-head bal__block-head--rose">
        <div>
          <div class="bal__block-kicker">Накопительные</div>
          <div class="bal__block-sum">{{ formatPoints(demo.earned) }}</div>
        </div>
      </header>
      <div v-if="demo.earnedLots.length" class="bal__lots">
        <div v-for="(lot, i) in demo.earnedLots" :key="'e' + i" class="bal__lot">
          <span class="bal__lot-pts">{{ formatPoints(lot.points) }} баллов</span>
          <span class="qp-expiry">сгорят {{ formatDateShort(lot.expires_at) }}</span>
        </div>
      </div>
      <div v-else class="bal__empty">Пока нет накопительных баллов</div>
    </section>

    <section class="bal__block qp-card qp-card--gold">
      <header class="bal__block-head bal__block-head--gold">
        <div>
          <div class="bal__block-kicker">Подарочные</div>
          <div class="bal__block-sum">{{ formatPoints(demo.gift) }}</div>
        </div>
      </header>
      <div v-if="demo.giftLots.length" class="bal__lots">
        <div v-for="(lot, i) in demo.giftLots" :key="'g' + i" class="bal__lot">
          <span class="bal__lot-pts">{{ formatPoints(lot.points) }} баллов</span>
          <span class="qp-expiry">сгорят {{ formatDateShort(lot.expires_at) }}</span>
        </div>
      </div>
      <div v-else class="bal__empty">Пока нет подарочных баллов</div>
    </section>

    <section v-if="demo.nearest" class="bal__near">
      <span class="bal__near-ico" aria-hidden="true">◷</span>
      <div>
        <div class="bal__near-label">Ближайшее сгорание</div>
        <div class="bal__near-text">
          {{ formatPoints(demo.nearest.points) }} баллов ·
          <span class="bal__near-date">{{ formatDateLong(demo.nearest.expires_at) }}</span>
        </div>
      </div>
    </section>

    <p class="bal__foot">Стиль × качество × выгода</p>
  </div>
</template>

<script setup lang="ts">
import {
  formatDateLong,
  formatDateShort,
  formatPoints,
  useDesignDemo,
} from "./useDesignDemo";

const demo = useDesignDemo();
</script>

<style scoped>
.bal__hero {
  margin-top: 22px;
  padding: 28px 22px 24px;
  text-align: center;
  background:
    linear-gradient(145deg, rgba(197, 143, 157, 0.9), rgba(176, 118, 134, 0.86)),
    url("/app/design/bg-silk.png") center/cover;
  color: #fffaf7;
  position: relative;
  overflow: hidden;
}

.bal__hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 40%);
  pointer-events: none;
}

.bal__hero-label,
.bal__hero-value,
.bal__hero-unit,
.bal__hero-eq,
.bal__hero-badge {
  position: relative;
  z-index: 1;
}

.bal__hero-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  opacity: 0.9;
}

.bal__hero-value {
  margin-top: 10px;
  font-family: var(--qp-serif);
  font-size: clamp(3.2rem, 15vw, 4.2rem);
  font-weight: 700;
  line-height: 0.95;
  letter-spacing: 0.02em;
  animation: qpFadeUp 0.9s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
}

.bal__hero-unit {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  opacity: 0.92;
}

.bal__hero-eq {
  margin-top: 10px;
  font-size: 15px;
  font-weight: 600;
  opacity: 0.88;
}

.bal__hero-badge {
  display: inline-block;
  margin-top: 16px;
  padding: 7px 14px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.bal__block {
  margin-top: 14px;
  padding: 18px 18px 14px;
}

.bal__block-kicker {
  font-size: 12px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-weight: 800;
}

.bal__block-head--rose .bal__block-kicker {
  color: var(--qp-rose);
}

.bal__block-head--gold .bal__block-kicker {
  color: var(--qp-gold-deep);
}

.bal__block-sum {
  margin-top: 8px;
  font-family: var(--qp-serif);
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--qp-ink);
  line-height: 1;
}

.bal__lots {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bal__lot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding-top: 12px;
  border-top: 1px solid rgba(57, 37, 45, 0.1);
}

.bal__lot-pts {
  font-size: 15px;
  font-weight: 700;
  color: var(--qp-ink);
}

.bal__empty {
  margin-top: 12px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(23, 21, 23, 0.5);
}

.bal__near {
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, #1c1618, #2a2024);
  color: #f7f1ea;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid rgba(180, 154, 106, 0.35);
  box-shadow: 0 0 0 3px rgba(180, 154, 106, 0.1);
}

.bal__near-ico {
  color: var(--qp-gold);
  font-size: 18px;
}

.bal__near-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  opacity: 0.75;
}

.bal__near-text {
  margin-top: 4px;
  font-size: 15px;
  font-weight: 600;
}

.bal__near-date {
  color: #e4c997;
  font-weight: 800;
}

.bal__foot {
  margin: 28px 0 8px;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(23, 21, 23, 0.4);
}
</style>
