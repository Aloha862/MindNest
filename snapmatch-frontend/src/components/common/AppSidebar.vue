<template>
  <aside class="admin-sidebar">
    <div class="brand"><Logo size="sm" /></div>
    <nav>
      <RouterLink v-for="item in items" :key="item.to" :to="item.to">
        <component :is="item.icon" />
        {{ item.label }}
      </RouterLink>
    </nav>
    <RouterLink class="back-link" to="/user/dashboard"><Home />返回用户端</RouterLink>
  </aside>
</template>

<script setup>
import Logo from './Logo.vue'
import { BookOpen, Cpu, FileImage, Home, LayoutDashboard, ScrollText, Settings, Users } from 'lucide-vue-next'

const items = [
  { to: '/admin/dashboard', label: '后台首页', icon: LayoutDashboard },
  { to: '/admin/users', label: '用户管理', icon: Users },
  { to: '/admin/files', label: '文件管理', icon: FileImage },
  { to: '/admin/tasks', label: '识别任务', icon: Cpu },
  { to: '/admin/questions', label: '题目管理', icon: BookOpen },
  { to: '/admin/model-logs', label: '模型日志', icon: ScrollText },
  { to: '/admin/system-config', label: '系统配置', icon: Settings }
]
</script>

<style scoped>
.admin-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 25;
  width: var(--sm-admin-sidebar);
  border-right: 1px solid var(--sm-border);
  background: #fff;
}

.brand {
  height: 96px;
  padding: 24px;
  border-bottom: 1px solid var(--sm-border);
}

nav {
  display: grid;
  gap: 10px;
  padding: 20px 14px;
}

nav a,
.back-link {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 0 12px;
  border-radius: 9px;
  color: var(--sm-text-2);
  font-size: 14px;
}

nav a.router-link-active {
  color: #fff;
  background: var(--sm-primary);
  box-shadow: 0 10px 18px rgba(59, 130, 246, 0.24);
  font-weight: 700;
}

svg {
  width: 17px;
}

.back-link {
  position: absolute;
  right: 14px;
  bottom: 16px;
  left: 14px;
  color: var(--sm-muted);
  border-top: 1px solid var(--sm-border);
  border-radius: 0;
  padding-top: 16px;
}

@media (max-width: 900px) {
  .admin-sidebar {
    display: none;
  }
}
</style>
