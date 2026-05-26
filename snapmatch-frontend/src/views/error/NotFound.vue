<template>
  <main class="error-page">
    <section class="panel">
      <Warning />
      <h1>404</h1>
      <p>页面不存在或已被移动。</p>
      <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
    </section>
  </main>
</template>

<script setup>
import { Warning } from '@element-plus/icons-vue'
</script>

<style scoped>
.error-page {
  display: grid;
  min-height: 100vh;
  place-items: center;
}

.panel {
  display: grid;
  place-items: center;
  width: 360px;
  padding: 40px;
  text-align: center;
}

svg {
  width: 48px;
  color: var(--sm-warning);
}

h1 {
  margin: 10px 0;
  font-size: 56px;
}

p {
  color: var(--sm-muted);
}
</style>
