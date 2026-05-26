<template>
  <header class="user-header">
    <div class="header-inner">
      <Logo />
      <nav>
        <RouterLink v-for="item in desktopItems" :key="item.to" :to="item.to">
          <component :is="item.icon" />
          {{ item.label }}
        </RouterLink>
      </nav>
      <div class="header-actions">
        <RouterLink v-if="auth.role === 'admin'" class="admin-link" to="/admin/dashboard">进入后台</RouterLink>
        <el-dropdown trigger="click" @command="onCommand">
          <button class="user-pill" type="button">
            <span>{{ user?.avatar || userInitial }}</span>
            {{ user?.nickname || user?.username || '用户' }}
            <ChevronDown />
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile"><UserRound />个人中心</el-dropdown-item>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item divided command="logout"><LogOut />退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import Logo from './Logo.vue'
import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  Download,
  FolderTree,
  History,
  LayoutDashboard,
  LogOut,
  Upload,
  UserRound
} from 'lucide-vue-next'

const desktopItems = [
  { to: '/user/dashboard', label: '首页', icon: LayoutDashboard },
  { to: '/user/upload', label: '上传识别', icon: Upload },
  { to: '/user/history', label: '识别记录', icon: History },
  { to: '/user/questions', label: '题目卡片', icon: BookOpen },
  { to: '/user/subjects', label: '科目分类', icon: FolderTree },
  { to: '/user/wrong-questions', label: '错题本', icon: AlertCircle },
  { to: '/user/export', label: '导出中心', icon: Download },
  { to: '/user/profile', label: '个人中心', icon: UserRound }
]

const router = useRouter()
const auth = useAuthStore()
const user = computed(() => auth.userInfo)
const userInitial = computed(() => (user.value?.nickname || user.value?.username || '用').slice(0, 1))

async function onCommand(command) {
  if (command === 'profile') router.push('/user/profile')
  if (command === 'password') router.push('/change-password')
  if (command === 'logout') {
    await auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.user-header {
  position: sticky;
  top: 0;
  z-index: 20;
  height: var(--sm-header-height);
  border-bottom: 1px solid var(--sm-border);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(16px);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: min(var(--sm-content), calc(100vw - 48px));
  height: 100%;
  margin: 0 auto;
  gap: 18px;
}

nav {
  display: flex;
  flex: 1;
  justify-content: center;
  gap: 5px;
  min-width: 0;
}

nav a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-radius: 10px;
  color: var(--sm-muted);
  font-size: 14px;
  white-space: nowrap;
}

nav a.router-link-active {
  color: var(--sm-primary-dark);
  background: var(--sm-soft);
  font-weight: 700;
}

nav svg {
  width: 16px;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.admin-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border: 1px solid var(--sm-border);
  border-radius: 10px;
  color: var(--sm-text-2);
  font-size: 13px;
  background: #fff;
}

.user-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  background: transparent;
  color: var(--sm-text);
  font-weight: 600;
  cursor: pointer;
}

.user-pill span {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, var(--sm-primary), var(--sm-ai));
}

.user-pill svg {
  width: 14px;
  color: var(--sm-muted);
}

:deep(.el-dropdown-menu__item svg) {
  width: 16px;
  margin-right: 8px;
}

@media (max-width: 1180px) {
  nav a {
    padding: 8px;
    font-size: 13px;
  }
}

@media (max-width: 980px) {
  nav,
  .admin-link {
    display: none;
  }

  .header-inner {
    width: min(100% - 24px, var(--sm-content));
  }
}
</style>
