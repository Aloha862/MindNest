<template>
  <header class="page-header">
    <div>
      <h1>{{ title }}</h1>
      <p v-if="subtitle">{{ subtitle }}</p>
    </div>
    <slot />
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin: 28px 0 22px;
}

h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
  font-weight: 850;
}

p {
  margin: 8px 0 0;
  color: var(--sm-muted);
}
</style>
