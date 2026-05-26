<template>
  <div class="panel error-block">
    <CircleCloseFilled />
    <strong>{{ title }}</strong>
    <p>{{ message }}</p>
    <el-button type="primary" @click="$emit('retry')">重试</el-button>
  </div>
</template>

<script setup>
defineEmits(['retry'])
defineProps({
  title: { type: String, default: '加载失败' },
  message: { type: String, default: '请检查网络或稍后再试。' }
})
</script>

<style scoped>
.error-block {
  display: grid;
  place-items: center;
  min-height: 260px;
  padding: 40px;
  text-align: center;
}

svg {
  width: 42px;
  height: 42px;
  color: var(--sm-danger);
}

strong {
  margin-top: 12px;
}

p {
  color: var(--sm-muted);
}
</style>
