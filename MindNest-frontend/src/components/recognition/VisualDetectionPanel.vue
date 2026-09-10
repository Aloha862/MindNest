<template>
  <section class="panel visual-panel">
    <header class="panel-head">
      <div>
        <h3>YOLO 视觉区域检测</h3>
        <p>检测题干、公式、解析、答案和手写批注等版面区域</p>
      </div>
      <span>{{ detections.length }} 个区域</span>
    </header>

    <el-skeleton v-if="pending" :rows="5" animated />

    <div v-if="detections.length" class="visual-grid">
      <div class="preview">
        <img :src="imageUrl" alt="YOLO 检测结果" />
        <i
          v-for="item in detections"
          :key="`${item.label}-${item.box?.x}-${item.box?.y}`"
          class="box"
          :style="boxStyle(item)"
        >
          <em>{{ item.labelName || item.label }}</em>
        </i>
      </div>
      <div class="detection-list">
        <div v-for="item in detections" :key="`${item.label}-${item.confidence}-${item.box?.x}`">
          <strong>{{ item.labelName || item.label }}</strong>
          <small>{{ Math.round((item.confidence || 0) * 100) }}%</small>
        </div>
      </div>
    </div>

    <el-empty v-if="!pending && !detections.length" description="暂无 YOLO 检测结果" />
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  imageUrl: { type: String, default: '' },
  yolo: { type: Object, default: () => ({}) },
  pending: { type: Boolean, default: false }
})

const detections = computed(() => props.yolo?.detections || [])

function boxStyle(item) {
  const imageWidth = props.yolo?.imageWidth || 1
  const imageHeight = props.yolo?.imageHeight || 1
  const box = item.bbox || item.box || {}
  return {
    left: `${((box.x || 0) / imageWidth) * 100}%`,
    top: `${((box.y || 0) / imageHeight) * 100}%`,
    width: `${((box.width || 0) / imageWidth) * 100}%`,
    height: `${((box.height || 0) / imageHeight) * 100}%`
  }
}
</script>

<style scoped>
.visual-panel {
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
  color: #0f766e;
  background: #ccfbf1;
  font-size: 12px;
}

.visual-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px;
  gap: 14px;
}

.preview {
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  background: #f8fafc;
}

.preview img {
  width: 100%;
  height: auto;
  display: block;
}

.box {
  position: absolute;
  border: 2px solid #2563eb;
  border-radius: 8px;
  background: rgba(37, 99, 235, 0.08);
  pointer-events: none;
}

.box em {
  position: absolute;
  left: 6px;
  top: 6px;
  padding: 3px 7px;
  border-radius: 999px;
  color: #fff;
  background: #2563eb;
  font-style: normal;
  font-size: 12px;
  white-space: nowrap;
}

.detection-list {
  display: grid;
  gap: 10px;
  align-content: start;
}

.detection-list div {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--sm-border);
  border-radius: 10px;
}

.detection-list small {
  color: var(--sm-muted);
}

@media (max-width: 760px) {
  .visual-grid {
    grid-template-columns: 1fr;
  }
}
</style>
