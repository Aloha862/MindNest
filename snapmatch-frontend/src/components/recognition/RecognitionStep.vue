<template>
  <section class="panel step-panel">
    <div class="task-line">
      <div>
        <h3>识别任务 · {{ task.id }}</h3>
        <p>{{ task.fileName }} · {{ task.currentStep }}</p>
      </div>
      <StatusTag :status="task.status" />
    </div>
    <el-progress :percentage="task.progress" :stroke-width="10" />
  </section>
</template>

<script setup>
import StatusTag from '@/components/common/StatusTag.vue'

defineProps({ task: { type: Object, required: true } })
</script>

<style scoped>
.step-panel {
  padding: 22px;
}

.task-line {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

h3,
p {
  margin: 0;
}

p {
  margin-top: 6px;
  color: var(--sm-muted);
}
</style>
