<template>
  <main class="page-shell about">
    <PageHeader title="关于智学空间(MindNest)" subtitle="从题目识别、错因分析到学习状态监督的多模态学习系统" />
    <section class="panel">
      <h2>项目定位</h2>
      <p>智学空间(MindNest)融合 OpenCV、YOLO、OCR、视觉语言模型和专注状态统计，用于把作业、试卷、错题图片和学习行为整理为可理解、可复盘、可复习的学习闭环。</p>
    </section>
  </main>
</template>

<script setup>
import PageHeader from '@/components/common/PageHeader.vue'
</script>

<style scoped>
.about {
  padding-bottom: 80px;
}

.panel {
  padding: 28px;
}

p {
  color: var(--sm-muted);
  line-height: 1.8;
}
</style>
