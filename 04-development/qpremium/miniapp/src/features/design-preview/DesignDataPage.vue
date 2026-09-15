<template>
  <div class="qp-fade data">
    <div class="qp-kicker">Ваш профиль</div>
    <h1 class="qp-title">Мои данные</h1>

    <section class="data__intro">
      <div class="data__name">{{ demo.fullName }}</div>
      <div class="data__badge">
        <span class="data__crown" aria-hidden="true">✦</span>
        Premium Member
      </div>
      <p class="data__tag">Больше, чем покупки. Это ваш клуб.</p>
    </section>

    <div class="qp-section-label"><span>Личная информация</span></div>

    <section class="data__list qp-card">
      <div class="data__row">
        <div>
          <div class="data__label">Имя</div>
          <div class="data__value">{{ demo.fullName }}</div>
        </div>
      </div>
      <div class="data__row">
        <div>
          <div class="data__label">Телефон</div>
          <div class="data__value">{{ demo.phone }}</div>
        </div>
      </div>
      <div class="data__row">
        <div>
          <div class="data__label">Email</div>
          <div class="data__value">{{ demo.email }}</div>
        </div>
      </div>
      <div class="data__row data__row--last">
        <div>
          <div class="data__label">Дата рождения</div>
          <div class="data__value">{{ formatBirth(demo.birthDate) }}</div>
          <div v-if="demo.pendingBirth" class="data__pending">
            Требует подтверждения → {{ formatBirth(demo.pendingBirth) }}
          </div>
        </div>
      </div>
    </section>

    <section class="data__privacy qp-card">
      <div class="data__privacy-title">Конфиденциальность</div>
      <div class="data__privacy-text">Ваши данные под защитой</div>
    </section>

    <p class="data__note">Превью дизайна: редактирование отключено</p>
  </div>
</template>

<script setup lang="ts">
import { formatBirth, useDesignDemo } from "./useDesignDemo";

const demo = useDesignDemo();
</script>

<style scoped>
.data__intro {
  margin-top: 22px;
}

.data__name {
  font-family: var(--qp-serif);
  font-size: 2.05rem;
  font-weight: 700;
  color: var(--qp-ink);
  line-height: 1.15;
}

.data__badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--qp-gold-deep);
  font-weight: 700;
}

.data__crown {
  font-size: 11px;
}

.data__tag {
  margin: 10px 0 0;
  font-size: 15px;
  font-weight: 500;
  color: rgba(23, 21, 23, 0.65);
  max-width: 32ch;
}

.data__list {
  padding: 4px 18px;
}

.data__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(57, 37, 45, 0.08);
}

.data__row--last {
  border-bottom: 0;
}

.data__label {
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(23, 21, 23, 0.5);
  font-weight: 700;
}

.data__value {
  margin-top: 5px;
  font-size: 16px;
  font-weight: 600;
  color: var(--qp-ink);
}

.data__pending {
  margin-top: 6px;
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(197, 143, 157, 0.18);
  color: #8a5463;
  font-size: 11px;
}

.data__privacy {
  margin-top: 16px;
  padding: 16px 18px;
  background: linear-gradient(135deg, rgba(232, 218, 218, 0.55), rgba(255, 252, 249, 0.9));
}

.data__privacy-title {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  font-weight: 800;
  color: var(--qp-rose);
}

.data__privacy-text {
  margin-top: 5px;
  font-size: 15px;
  font-weight: 600;
  color: var(--qp-ink-soft);
}

.data__note {
  margin: 20px 0 8px;
  text-align: center;
  font-size: 11px;
  color: rgba(23, 21, 23, 0.35);
}
</style>
