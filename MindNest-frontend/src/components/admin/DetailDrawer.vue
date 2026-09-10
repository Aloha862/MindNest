<template>
  <el-drawer :model-value="modelValue" title="详情" size="420px" @close="$emit('update:modelValue', false)">
    <slot />
  </el-drawer>
</template>

<script setup>
defineEmits(['update:modelValue'])
defineProps({ modelValue: { type: Boolean, default: false } })
</script>
