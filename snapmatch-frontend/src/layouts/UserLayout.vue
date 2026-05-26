<template>
  <div>
    <AppHeader />
    <main class="user-main">
      <RouterView />
    </main>
    <nav class="mobile-nav">
      <RouterLink to="/user/dashboard"><LayoutDashboard />首页</RouterLink>
      <RouterLink to="/user/upload"><Upload />上传</RouterLink>
      <RouterLink to="/user/history"><History />记录</RouterLink>
      <RouterLink to="/user/questions"><BookOpen />题目</RouterLink>
      <RouterLink to="/user/profile"><UserRound />我的</RouterLink>
    </nav>
  </div>
</template>

<script setup>
import AppHeader from '@/components/common/AppHeader.vue'
import { BookOpen, History, LayoutDashboard, Upload, UserRound } from 'lucide-vue-next'
</script>

<style scoped>
.user-main {
  min-height: calc(100vh - var(--sm-header-height));
  padding: 1px 0 72px;
}

.mobile-nav {
  display: none;
}

@media (max-width: 768px) {
  .mobile-nav {
    position: fixed;
    inset: auto 0 0 0;
    z-index: 30;
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    border-top: 1px solid var(--sm-border);
    background: rgba(255, 255, 255, 0.96);
    backdrop-filter: blur(16px);
  }

  .mobile-nav a {
    display: grid;
    place-items: center;
    gap: 3px;
    padding: 8px 0;
    color: var(--sm-muted);
    font-size: 12px;
  }

  .mobile-nav a.router-link-active {
    color: var(--sm-primary);
    font-weight: 700;
  }

  .mobile-nav svg {
    width: 18px;
  }
}
</style>
