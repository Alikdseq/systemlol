<template>
  <div class="qp-fade rules">
    <div class="qp-kicker">Программы лояльности</div>
    <h1 class="qp-title">Как работает<br />Q Premium</h1>
    <p class="qp-lead">Получайте больше с каждой покупкой.</p>

    <div class="rules__grid">
      <article class="rules__card qp-card">
        <div class="rules__num">01</div>
        <div class="rules__value">{{ demo.accrualPercent }}%</div>
        <div class="rules__label">Начисление</div>
        <div class="rules__hint">за покупку</div>
      </article>
      <article class="rules__card qp-card">
        <div class="rules__num">02</div>
        <div class="rules__value">1 ₽</div>
        <div class="rules__label">Стоимость</div>
        <div class="rules__hint">1 балла</div>
      </article>
      <article class="rules__card qp-card">
        <div class="rules__num">03</div>
        <div class="rules__value rules__value--sm">{{ monthsApprox(demo.earnedTtlDays) }}</div>
        <div class="rules__label">Срок</div>
        <div class="rules__hint">накопительных</div>
      </article>
      <article class="rules__card qp-card">
        <div class="rules__num">04</div>
        <div class="rules__value rules__value--sm">{{ daysLabel(demo.giftTtlDays).toUpperCase() }}</div>
        <div class="rules__label">Срок</div>
        <div class="rules__hint">подарочных</div>
      </article>
    </div>

    <article class="rules__wide qp-card">
      <div class="rules__num">05</div>
      <div class="rules__value">{{ demo.maxRedeemPercent }}%</div>
      <div class="rules__label">Максимальная оплата</div>
      <div class="rules__hint">покупки баллами</div>
    </article>

    <article class="rules__other qp-card">
      <div class="rules__other-kicker">Другие условия</div>
      <div class="rules__other-text">
        {{ demo.rulesText || "Полные условия программы лояльности задаёт администратор в настройках." }}
      </div>
    </article>

    <section class="rules__important">
      <div class="rules__important-title">✦ Важно</div>
      <ul>
        <li>Баллы начисляются за покупки в магазинах программы.</li>
        <li>Срок действия виден по каждой партии на экране баланса.</li>
        <li>Списание баллов рассчитывает система — кассир сумму не вводит вручную.</li>
      </ul>
      <div class="rules__script">Больше чем просто покупки</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { daysLabel, monthsApprox, useDesignDemo } from "./useDesignDemo";

const demo = useDesignDemo();
</script>

<style scoped>
.rules__grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.rules__card,
.rules__wide {
  padding: 16px;
  min-height: 132px;
}

.rules__wide {
  margin-top: 12px;
}

.rules__num {
  font-size: 11px;
  letter-spacing: 0.16em;
  color: rgba(23, 21, 23, 0.4);
  font-weight: 700;
}

.rules__value {
  margin-top: 10px;
  font-family: var(--qp-serif);
  font-size: 2.15rem;
  font-weight: 700;
  line-height: 1;
  color: var(--qp-ink);
}

.rules__value--sm {
  font-size: 1.25rem;
  letter-spacing: 0.04em;
  line-height: 1.2;
}

.rules__label {
  margin-top: 10px;
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-weight: 800;
  color: var(--qp-rose);
}

.rules__hint {
  margin-top: 5px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(23, 21, 23, 0.58);
}

.rules__other {
  margin-top: 12px;
  padding: 18px;
}

.rules__other-kicker {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: 800;
  color: var(--qp-gold-deep);
}

.rules__other-text {
  margin-top: 10px;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.55;
  color: var(--qp-ink-soft);
  white-space: pre-wrap;
}

.rules__important {
  margin-top: 16px;
  padding: 20px 18px 18px;
  border-radius: var(--qp-radius);
  background:
    linear-gradient(160deg, rgba(28, 22, 24, 0.94), rgba(40, 28, 32, 0.92)),
    url("/app/design/bg-dark.png") center/cover;
  color: #f7f1ea;
  position: relative;
  overflow: hidden;
}

.rules__important-title {
  font-size: 11px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--qp-gold);
  font-weight: 700;
}

.rules__important ul {
  margin: 14px 0 0;
  padding: 0 0 0 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rules__important li {
  position: relative;
  padding-left: 14px;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  opacity: 0.94;
}

.rules__important li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.55em;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--qp-rose);
}

.rules__script {
  margin-top: 18px;
  text-align: right;
  font-family: var(--qp-serif);
  font-style: italic;
  font-size: 15px;
  color: rgba(180, 154, 106, 0.9);
}
</style>
