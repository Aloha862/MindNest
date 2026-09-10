<template>
  <article class="stat-card panel" :class="{ compact }">
    <div>
      <p>{{ label }}</p>
      <strong>{{ value }}</strong>
      <small>{{ hint }}</small>
    </div>
    <span :style="{ background: color + '18', color }"><component :is="icon" /></span>
  </article>
</template>

<script setup>
import { BarChart3 } from 'lucide-vue-next'

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: '' },
  color: { type: String, default: '#3b82f6' },
  icon: { type: [Object, Function], default: BarChart3 },
  compact: { type: Boolean, default: false }
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 96px;
  padding: 20px;
}

.compact {
  min-height: 70px;
}

p,
small {
  margin: 0;
  color: var(--sm-muted);
}

strong {
  display: block;
  margin: 8px 0 6px;
  font-size: 26px;
  line-height: 1;
}

span {
  display: inline-grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
}

svg {
  width: 20px;
  height: 20px;
}
</style>
