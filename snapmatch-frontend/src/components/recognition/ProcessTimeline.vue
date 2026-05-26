<template>
  <section class="panel timeline-panel">
    <h3>处理步骤</h3>
    <el-timeline>
      <el-timeline-item v-for="step in steps" :key="step.title" :timestamp="step.time" :type="step.type">
        {{ step.title }}
      </el-timeline-item>
    </el-timeline>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'pending' }
})

const order = ['pending', 'preprocessing', 'yolo_running', 'ocr_running', 'formula_running', 'vlm_running', 'parsing', 'persisting', 'completed', 'needs_review']
const currentIndex = computed(() => {
  if (props.status === 'failed') return order.length
  return Math.max(order.indexOf(props.status), 0)
})

const steps = computed(() => [
  { title: '图片上传完成', time: '已创建', type: currentIndex.value >= 0 ? 'success' : 'info' },
  { title: 'OpenCV 图像预处理', time: '预处理', type: currentIndex.value >= 1 ? 'primary' : 'info' },
  { title: 'YOLO 视觉区域检测', time: '检测题干/公式/解析', type: currentIndex.value >= 2 ? 'primary' : 'info' },
  { title: 'OCR 文字识别', time: '识别文本', type: currentIndex.value >= 3 ? 'primary' : 'info' },
  { title: '公式识别与融合', time: 'LaTeX / 文本对齐', type: currentIndex.value >= 4 ? 'primary' : 'info' },
  { title: 'VLM 题目结构分析', time: '结构化', type: currentIndex.value >= 5 ? 'warning' : 'info' },
  { title: '结构校验与写库', time: '生成题卡', type: currentIndex.value >= 7 ? 'primary' : 'info' },
  { title: props.status === 'failed' ? '识别失败' : props.status === 'needs_review' ? '等待复核' : '题目卡片生成', time: props.status === 'completed' ? '已完成' : props.status === 'needs_review' ? '建议复核' : '等待中', type: props.status === 'failed' ? 'danger' : currentIndex.value >= 8 ? 'success' : 'info' }
])
</script>

<style scoped>
.timeline-panel {
  padding: 22px;
}
</style>
