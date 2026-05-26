<template>
  <main class="auth-layout">
    <section class="auth-side grid-bg">
      <Logo size="lg" />
      <div class="pitch">
        <h1>多模态题目理解，让个性化复习 <span>一拍即合</span></h1>
        <p>融合 OpenCV、YOLO、OCR 与视觉语言模型，把题目图片转化为可解析、可检索、可复习的智能题库。</p>
        <ul>
          <li><ScanLine />OpenCV + YOLO 版面理解</li>
          <li><Sparkles />VLM 结构化解析与复习建议</li>
          <li><Layers />按科目/题型/知识点自动分类</li>
        </ul>
      </div>
      <AppFooter />
    </section>
    <section class="auth-form">
      <slot />
    </section>
  </main>
</template>

<script setup>
import Logo from '@/components/common/Logo.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import { Layers, ScanLine, Sparkles } from 'lucide-vue-next'
</script>

<style scoped>
.auth-layout {
  display: grid;
  grid-template-columns: 1.08fr 1fr;
  min-height: 100vh;
  background: linear-gradient(135deg, #eef2ff 0%, #f6f8fc 40%, #f5f3ff 100%);
}

.auth-side {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px 56px;
}

.pitch {
  max-width: 520px;
}

h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.22;
  font-weight: 900;
}

h1 span {
  color: var(--sm-primary);
}

p {
  color: var(--sm-muted);
  line-height: 1.7;
}

ul {
  display: grid;
  gap: 12px;
  padding: 0;
  margin: 28px 0 0;
  list-style: none;
}

li {
  display: flex;
  gap: 14px;
  align-items: center;
  width: 420px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
}

li svg {
  width: 22px;
  color: var(--sm-primary);
}

.auth-form {
  display: grid;
  place-items: center;
  padding: 40px;
  background: rgba(247, 247, 251, 0.72);
}

@media (max-width: 900px) {
  .auth-layout {
    grid-template-columns: 1fr;
  }

  .auth-side {
    display: none;
  }
}
</style>
