<template>
  <el-dialog :model-value="modelValue" title="确认操作" width="360px" @close="$emit('update:modelValue', false)">
    <p>{{ message }}</p>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="danger" @click="$emit('confirm')">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
defineEmits(['update:modelValue', 'confirm'])
defineProps({
  modelValue: { type: Boolean, default: false },
  message: { type: String, default: '确定执行该操作吗？' }
})
</script>
