<template>
  <span class="status-tag" :class="variant">
    <i />
    {{ label || statusText(status) }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { statusText } from '@/utils/format'

const props = defineProps({
  status: { type: String, default: '' },
  label: { type: String, default: '' }
})

const variant = computed(() => {
  if (['completed', 'recognized', 'active', 'success'].includes(props.status)) return 'success'
  if (['vlm_running', 'ocr_running', 'yolo_running', 'formula_running', 'parsing', 'persisting', 'processing'].includes(props.status)) return 'primary'
  if (['needs_review'].includes(props.status)) return 'warning'
  if (['pending', 'uploaded'].includes(props.status)) return 'muted'
  if (['failed', 'disabled'].includes(props.status)) return 'danger'
  return 'primary'
})
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
  gap: 6px;
  min-width: 64px;
  width: max-content;
  max-width: 100%;
  white-space: nowrap;
  padding: 5px 11px;
  border-radius: 999px;
  line-height: 1;
  font-size: 12px;
  font-weight: 600;
  box-sizing: border-box;
}

i {
  flex: none;
  width: 6px;
  height: 6px;
  border-radius: 999px;
}

.success {
  color: #16a34a;
  background: #dcfce7;
}

.primary {
  color: #7c3aed;
  background: #ede9fe;
}

.danger {
  color: #dc2626;
  background: #fee2e2;
}

.warning {
  color: #b45309;
  background: #fef3c7;
}

.muted {
  color: #6b7280;
  background: #f3f4f6;
}

.success i { background: #22c55e; }
.primary i { background: #8b5cf6; }
.danger i { background: #ef4444; }
.warning i { background: #f59e0b; }
.muted i { background: #9ca3af; }
</style>
