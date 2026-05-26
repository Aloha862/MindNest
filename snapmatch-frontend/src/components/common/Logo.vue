<template>
  <RouterLink class="logo" :class="size" to="/">
    <span class="logo-mark"><Camera /></span>
    <span class="logo-copy">
      <strong>一拍即合 <b>SnapMatch</b></strong>
      <small v-if="size !== 'sm'">多模态理解 · 个性化复习</small>
    </span>
  </RouterLink>
</template>

<script setup>
import { Camera } from 'lucide-vue-next'

defineProps({
  size: { type: String, default: 'md' }
})
</script>

<style scoped>
.logo {
  display: inline-flex;
  gap: 10px;
  align-items: center;
  color: var(--sm-text);
}

.logo-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, var(--sm-primary), var(--sm-ai));
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.28);
}

.sm .logo-mark {
  width: 28px;
  height: 28px;
  border-radius: 10px;
}

.lg .logo-mark {
  width: 40px;
  height: 40px;
}

.logo-mark svg {
  width: 50%;
  height: 50%;
}

.logo-copy {
  display: block;
  line-height: 1.15;
}

strong {
  font-size: 18px;
  font-weight: 600;
}

b {
  color: var(--sm-primary);
  font-weight: 600;
}

small {
  display: block;
  margin-top: 3px;
  color: var(--sm-muted);
  font-size: 11px;
}

.lg strong {
  font-size: 24px;
}
</style>
