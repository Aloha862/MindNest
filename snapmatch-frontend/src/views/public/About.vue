<template>
  <main class="page-shell about">
    <PageHeader title="关于 SnapMatch" subtitle="面向学习场景的多模态智能题目理解与个性化复习平台" />
    <section class="panel">
      <h2>项目定位</h2>
      <p>一拍即合融合 OpenCV、YOLO、OCR、视觉语言模型和知识点统计，用于把作业、试卷和错题图片整理为可理解、可检索、可复习的智能题库。</p>
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
