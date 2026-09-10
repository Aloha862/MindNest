<template>
  <section class="panel result-panel">
    <header class="panel-head">
      <div>
        <h3>OCR 文字识别</h3>
        <p>完整展示 OCR 返回的识别文本，数学公式按原文位置保留</p>
      </div>
      <span>{{ lineCount ? `${lineCount} 行` : '文本' }}</span>
    </header>

    <el-skeleton v-if="pending" :rows="5" animated />

    <div v-else class="ocr-text">
      <MathText :text="displayText || '暂无 OCR 文本'" />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import MathText from '@/components/common/MathText.vue'

const props = defineProps({
  result: { type: Object, required: true },
  pending: { type: Boolean, default: false }
})

const displayText = computed(() => {
  if (props.result.rawText) return props.result.rawText
  const lines = []
  for (const section of props.result.sections || []) {
    for (const line of section.lines || []) {
      if (line?.text) lines.push(line.text)
    }
  }
  return lines.join('\n')
})

const lineCount = computed(() => displayText.value.split(/\r?\n/).filter((line) => line.trim()).length)
</script>

<style scoped>
.result-panel {
  padding: 22px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

h3,
p {
  margin: 0;
}

.panel-head p {
  margin-top: 6px;
  color: var(--sm-muted);
  font-size: 13px;
}

.panel-head > span {
  flex: none;
  padding: 5px 10px;
  border-radius: 999px;
  color: #2563eb;
  background: #eff6ff;
  font-size: 12px;
}

.ocr-text {
  min-height: 160px;
  padding: 16px;
  overflow: hidden;
  border: 1px solid var(--sm-border);
  border-radius: 12px;
  background: #fff;
  color: #111827;
  font-size: 15px;
  line-height: 1.9;
}

.ocr-text :deep(.math-line) {
  margin: 0;
}

.ocr-text :deep(.math-line + .math-line) {
  margin-top: 8px;
}

.ocr-text :deep(.math-inline) {
  max-width: none;
  overflow: visible;
  white-space: nowrap;
  vertical-align: middle;
}
</style>
