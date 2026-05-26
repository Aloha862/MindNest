<template>
  <main class="landing">
    <header class="landing-nav glass-bar">
      <div class="nav-inner">
        <Logo size="sm" />
        <nav>
          <RouterLink class="ghost" to="/login">登录</RouterLink>
          <RouterLink class="primary-link" to="/register">免费注册</RouterLink>
        </nav>
      </div>
    </header>

    <section class="hero">
      <div class="hero-grid page-shell">
        <div class="hero-copy">
          <span class="eyebrow"><Sparkles />面向学习场景的多模态智能题目理解平台</span>
          <h1>题目理解，个性复习<br />让学习闭环 <b>一拍即合</b></h1>
          <p>
            SnapMatch 通过 OpenCV 图像预处理、YOLO 区域检测、OCR 公式识别和视觉语言模型理解，
            把作业、试卷、错题图片整理成题目卡片、知识点画像与个性化复习建议。
          </p>
          <div class="actions">
            <RouterLink class="primary-link large" to="/register">开始体验<ArrowRight /></RouterLink>
            <RouterLink class="outline-link large" to="/login">使用演示账号</RouterLink>
          </div>
          <div class="metrics">
            <div><strong>3 步</strong><span>拍照 · 识别 · 整理</span></div>
            <div><strong>6+</strong><span>支持科目分类</span></div>
            <div><strong>VLM</strong><span>视觉语言模型</span></div>
          </div>
        </div>

        <div class="hero-card-wrap">
          <div class="hero-glow" />
          <article class="hero-card">
            <header>
              <span>识别任务 · #SM-20260520</span>
              <StatusTag status="completed" />
            </header>
            <div class="pipeline">
              <div><Camera /><span>图像预处理</span></div>
              <div><ScanLine /><span>区域与 OCR</span></div>
              <div><Cpu /><span>VLM 分析</span></div>
            </div>
            <section class="question-preview">
              <small>生成题目卡片 · 数学</small>
              <strong>已知函数 f(x)=x²+2x，求 f'(x)。</strong>
              <p><em>导数</em><em>基础</em><em>求导公式</em></p>
            </section>
          </article>
        </div>
      </div>
    </section>

    <section class="flow page-shell">
      <div class="section-head">
        <h2>为学习设计的多模态理解流程</h2>
        <p>不只是识别文字，更理解题目结构、解题路径与薄弱知识点</p>
      </div>
      <div class="flow-grid">
        <article v-for="item in features" :key="item.title">
          <span><component :is="item.icon" /></span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
        </article>
      </div>
    </section>

    <section class="cta page-shell">
      <ShieldCheck />
      <h2>立即开始你的智能学习整理</h2>
      <p>注册账号即可上传第一张图片，演示账号同样支持完整流程体验</p>
      <div>
        <RouterLink class="secondary-cta" to="/register">免费注册</RouterLink>
        <RouterLink class="white-outline" to="/login">登录</RouterLink>
      </div>
    </section>

    <AppFooter />
  </main>
</template>

<script setup>
import {
  ArrowRight,
  Camera,
  Cpu,
  Layers,
  ScanLine,
  ShieldCheck,
  Sparkles
} from 'lucide-vue-next'
import Logo from '@/components/common/Logo.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import AppFooter from '@/components/common/AppFooter.vue'

const features = [
  { icon: Camera, title: '上传图片', description: '支持拖拽上传作业、试卷、错题照片' },
  { icon: ScanLine, title: '区域与 OCR', description: '结合 YOLO 和视觉 OCR，提取题干、选项和公式' },
  { icon: Sparkles, title: 'VLM 理解', description: '生成答案解析、知识点和复习建议' },
  { icon: Layers, title: '智能分类', description: '按科目、题型、难度、知识点分类管理' }
]
</script>

<style scoped>
.landing {
  min-height: 100vh;
  background: var(--sm-bg);
}

.landing-nav {
  position: sticky;
  top: 0;
  z-index: 30;
}

.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(1200px, calc(100vw - 48px));
  height: 64px;
  margin: 0 auto;
}

.landing-nav nav,
.actions,
.cta div {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ghost,
.primary-link,
.outline-link,
.secondary-cta,
.white-outline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 16px;
  border-radius: 10px;
  font-weight: 600;
}

.primary-link {
  color: #fff;
  background: var(--sm-primary);
}

.primary-link:hover {
  background: var(--sm-primary-dark);
}

.outline-link {
  border: 1px solid var(--sm-border);
  background: #fff;
}

.large {
  min-height: 44px;
  padding-inline: 24px;
}

.hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #eef2ff 0%, #f6f8fc 60%, #fff 100%);
}

.hero::before {
  position: absolute;
  inset: 0;
  content: '';
  opacity: 0.05;
  background-image:
    linear-gradient(#111 1px, transparent 1px),
    linear-gradient(90deg, #111 1px, transparent 1px);
  background-size: 32px 32px;
}

.hero-grid {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 470px;
  gap: 80px;
  align-items: center;
  min-height: 620px;
  padding-block: 72px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  color: #7c3aed;
  background: #ede9fe;
  font-size: 12px;
  font-weight: 700;
}

h1 {
  margin: 20px 0 18px;
  font-size: 50px;
  line-height: 1.12;
  font-weight: 650;
}

h1 b {
  color: var(--sm-primary);
}

.hero-copy p {
  max-width: 520px;
  color: var(--sm-muted);
  line-height: 1.75;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  max-width: 450px;
  gap: 28px;
  margin-top: 28px;
}

.metrics strong {
  display: block;
  color: var(--sm-primary);
  font-size: 22px;
}

.metrics span {
  color: var(--sm-muted);
  font-size: 12px;
}

.hero-card-wrap {
  position: relative;
}

.hero-glow {
  position: absolute;
  inset: -16px;
  border-radius: 28px;
  background: linear-gradient(135deg, var(--sm-primary), var(--sm-ai));
  filter: blur(28px);
  opacity: 0.4;
}

.hero-card {
  position: relative;
  padding: 24px;
  border: 1px solid var(--sm-border);
  border-radius: 20px;
  background: #fff;
  box-shadow: var(--sm-shadow-strong);
}

.hero-card header,
.pipeline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hero-card header {
  margin-bottom: 20px;
  color: var(--sm-muted);
  font-size: 14px;
}

.pipeline {
  margin-bottom: 20px;
}

.pipeline div {
  flex: 1;
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 14px 10px;
  border-radius: 14px;
  background: rgba(238, 242, 255, 0.65);
  font-size: 12px;
}

.pipeline svg {
  color: var(--sm-primary);
}

.question-preview {
  padding: 18px;
  border-radius: 14px;
  background: rgba(238, 242, 255, 0.45);
}

.question-preview small {
  color: var(--sm-muted);
}

.question-preview strong {
  display: block;
  margin: 10px 0 12px;
}

.question-preview em {
  margin-right: 8px;
  padding: 4px 8px;
  border-radius: 7px;
  color: var(--sm-primary);
  background: rgba(59, 130, 246, 0.1);
  font-size: 12px;
  font-style: normal;
}

.flow {
  padding-block: 78px;
}

.section-head {
  margin-bottom: 42px;
  text-align: center;
}

.section-head h2,
.cta h2 {
  margin: 0 0 10px;
  font-size: 28px;
}

.section-head p,
.cta p {
  margin: 0;
  color: var(--sm-muted);
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.flow-grid article {
  padding: 24px;
  border: 1px solid var(--sm-border);
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.flow-grid span {
  display: inline-flex;
  width: 42px;
  height: 42px;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  border-radius: 14px;
  color: var(--sm-primary);
  background: rgba(59, 130, 246, 0.1);
}

.flow-grid h3 {
  margin: 0 0 8px;
}

.flow-grid p {
  margin: 0;
  color: var(--sm-muted);
  line-height: 1.65;
}

.cta {
  margin-bottom: 34px;
  padding: 48px 32px;
  border-radius: 28px;
  color: #fff;
  text-align: center;
  background: linear-gradient(135deg, var(--sm-primary) 0%, var(--sm-ai) 100%);
  overflow: hidden;
}

.cta > svg {
  width: 42px;
  height: 42px;
  margin-bottom: 16px;
  opacity: 0.85;
}

.cta p {
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 24px;
}

.cta div {
  justify-content: center;
}

.secondary-cta {
  color: var(--sm-text);
  background: #fff;
}

.white-outline {
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.45);
}

@media (max-width: 960px) {
  .hero-grid,
  .flow-grid {
    grid-template-columns: 1fr;
  }

  .hero-grid {
    gap: 40px;
    min-height: unset;
  }

  h1 {
    font-size: 38px;
  }
}

@media (max-width: 640px) {
  .nav-inner {
    width: calc(100vw - 24px);
  }

  .ghost {
    display: none;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .metrics {
    grid-template-columns: 1fr;
  }

  .primary-link,
  .outline-link {
    width: 100%;
  }
}
</style>
