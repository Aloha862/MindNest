<template>
  <div class="tag-group">
    <span v-for="tag in tags" :key="tag">#{{ tag }}</span>
  </div>
</template>

<script setup>
defineProps({ tags: { type: Array, default: () => [] } })
</script>

<style scoped>
.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

span {
  padding: 4px 7px;
  border-radius: 6px;
  color: #7c3aed;
  background: #f3e8ff;
  font-size: 12px;
  font-weight: 700;
}
</style>
