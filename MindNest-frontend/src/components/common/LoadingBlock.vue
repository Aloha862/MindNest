<template>
  <div class="panel loading-block">
    <el-skeleton animated :rows="rows" />
  </div>
</template>

<script setup>
defineProps({ rows: { type: Number, default: 5 } })
</script>

<style scoped>
.loading-block {
  padding: 24px;
}
</style>
