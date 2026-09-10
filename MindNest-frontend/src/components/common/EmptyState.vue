<template>
  <div class="empty panel">
    <DocumentRemove />
    <strong>{{ title }}</strong>
    <p>{{ description }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '当前筛选条件下没有可展示的内容。' }
})
</script>

<style scoped>
.empty {
  display: grid;
  place-items: center;
  min-height: 260px;
  padding: 40px;
  text-align: center;
}

svg {
  width: 44px;
  height: 44px;
  color: var(--sm-primary);
}

strong {
  margin-top: 14px;
  font-size: 18px;
}

p {
  margin: 8px 0 0;
  color: var(--sm-muted);
}
</style>
