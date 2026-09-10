<template>
  <div class="admin-layout">
    <AppSidebar />
    <section class="admin-content">
      <header class="admin-top">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>管理员控制台</el-breadcrumb-item>
          <el-breadcrumb-item>{{ title }}</el-breadcrumb-item>
        </el-breadcrumb>
        <el-dropdown trigger="click" @command="onCommand">
          <button class="admin-user" type="button">
            <span>{{ user?.avatar || userInitial }}</span>
            {{ user?.nickname || user?.username || '管理员' }}
            <ChevronDown />
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="user">返回用户端</el-dropdown-item>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>
      <main>
        <RouterView />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronDown } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'
import AppSidebar from '@/components/common/AppSidebar.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const user = computed(() => auth.userInfo)
const userInitial = computed(() => (user.value?.nickname || user.value?.username || '管').slice(0, 1))
const titleMap = {
  '/admin/dashboard': '后台首页',
  '/admin/users': '用户管理',
  '/admin/files': '文件管理',
  '/admin/tasks': '识别任务',
  '/admin/questions': '题目管理',
  '/admin/model-logs': '模型日志',
  '/admin/system-config': '系统配置'
}
const title = computed(() => {
  if (route.path.startsWith('/admin/tasks/')) return '识别任务详情'
  if (route.path.startsWith('/admin/questions/')) return '题目详情'
  return titleMap[route.path] || '后台首页'
})

async function onCommand(command) {
  if (command === 'user') router.push('/user/dashboard')
  if (command === 'password') router.push('/change-password')
  if (command === 'logout') {
    await auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.admin-content {
  min-height: 100vh;
  margin-left: var(--sm-admin-sidebar);
}

.admin-top {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--sm-header-height);
  padding: 0 24px;
  border-bottom: 1px solid var(--sm-border);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(16px);
}

.admin-user {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  background: transparent;
  color: var(--sm-text);
  font-weight: 600;
  cursor: pointer;
}

.admin-user span {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, var(--sm-primary), var(--sm-ai));
}

.admin-user svg {
  width: 14px;
  color: var(--sm-muted);
}

main {
  padding: 24px 24px 72px;
}

@media (max-width: 900px) {
  .admin-content {
    margin-left: 0;
  }

  main {
    padding: 18px 12px 72px;
  }
}
</style>
