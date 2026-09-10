<template>
  <header class="user-header">
    <div class="header-inner">
      <Logo class="brand" />

      <nav class="main-nav" aria-label="用户导航">
        <RouterLink v-for="item in primaryItems" :key="item.to" :to="item.to">
          <component :is="item.icon" />
          <span>{{ item.label }}</span>
        </RouterLink>

        <el-dropdown class="more-nav" trigger="click" @command="goNav">
          <button class="more-button" :class="{ active: isSecondaryActive }" type="button">
            <MoreHorizontal />
            <span>更多</span>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="item in secondaryItems" :key="item.to" :command="item.to">
                <component :is="item.icon" />
                {{ item.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </nav>

      <div class="header-actions">
        <RouterLink v-if="auth.role === 'admin'" class="admin-link" to="/admin/dashboard">进入后台</RouterLink>
        <el-dropdown trigger="click" @command="onCommand">
          <button class="user-pill" type="button">
            <span>{{ user?.avatar || userInitial }}</span>
            <strong>{{ user?.nickname || user?.username || '用户' }}</strong>
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
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import Logo from './Logo.vue'
import {
  Activity,
  AlertCircle,
  BookOpen,
  ChevronDown,
  Download,
  FileText,
  FolderTree,
  History,
  LayoutDashboard,
  LogOut,
  MoreHorizontal,
  Upload,
  UserRound
} from 'lucide-vue-next'

const primaryItems = [
  { to: '/user/dashboard', label: '首页', icon: LayoutDashboard },
  { to: '/user/upload', label: '上传识别', icon: Upload },
  { to: '/user/history', label: '识别记录', icon: History },
  { to: '/user/questions', label: '题目卡片', icon: BookOpen },
  { to: '/user/subjects', label: '科目分类', icon: FolderTree },
  { to: '/user/wrong-questions', label: '错题本', icon: AlertCircle }
]

const secondaryItems = [
  { to: '/user/focus', label: '专注监督', icon: Activity },
  { to: '/user/reports', label: '学习报告', icon: FileText },
  { to: '/user/export', label: '导出中心', icon: Download },
  { to: '/user/profile', label: '个人中心', icon: UserRound }
]

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const user = computed(() => auth.userInfo)
const userInitial = computed(() => (user.value?.nickname || user.value?.username || '用').slice(0, 1))
const isSecondaryActive = computed(() => secondaryItems.some((item) => route.path.startsWith(item.to)))

function goNav(path) {
  router.push(path)
}

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
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
}

.header-inner {
  display: grid;
  grid-template-columns: minmax(228px, 260px) minmax(0, 1fr) auto;
  align-items: center;
  width: min(var(--sm-content), calc(100vw - 48px));
  height: 100%;
  margin: 0 auto;
  gap: 18px;
}

.brand {
  min-width: 0;
}

.brand :deep(strong),
.brand :deep(small) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand :deep(strong) {
  font-size: 16px;
}

.main-nav {
  display: flex;
  justify-content: center;
  gap: 4px;
  min-width: 0;
}

.main-nav a,
.more-button,
.admin-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 11px;
  border-radius: 10px;
  color: var(--sm-muted);
  font-size: 14px;
  line-height: 1;
  white-space: nowrap;
  transition: color 0.16s ease, background 0.16s ease;
}

.main-nav a.router-link-active,
.more-button.active {
  color: var(--sm-primary-dark);
  background: var(--sm-soft);
  font-weight: 700;
}

.main-nav a:hover,
.more-button:hover,
.admin-link:hover {
  color: var(--sm-primary-dark);
  background: #f1f5ff;
}

.main-nav svg,
.more-button svg {
  width: 16px;
  height: 16px;
  flex: none;
}

.more-button {
  border: 0;
  background: transparent;
  cursor: pointer;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 0;
}

.admin-link {
  border: 1px solid var(--sm-border);
  background: #fff;
  color: var(--sm-text-2);
  font-size: 13px;
}

.user-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 168px;
  border: 0;
  background: transparent;
  color: var(--sm-text);
  font-weight: 600;
  cursor: pointer;
}

.user-pill span {
  display: inline-grid;
  place-items: center;
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  color: #fff;
  background: linear-gradient(135deg, var(--sm-primary), var(--sm-ai));
}

.user-pill strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.user-pill svg {
  width: 14px;
  color: var(--sm-muted);
  flex: none;
}

:deep(.el-dropdown-menu__item svg) {
  width: 16px;
  margin-right: 8px;
}

@media (max-width: 1180px) {
  .header-inner {
    grid-template-columns: minmax(188px, 210px) minmax(0, 1fr) auto;
    gap: 12px;
  }

  .brand :deep(small) {
    display: none;
  }

  .main-nav a,
  .more-button {
    padding: 0 8px;
    font-size: 13px;
  }
}

@media (max-width: 980px) {
  .main-nav,
  .admin-link {
    display: none;
  }

  .header-inner {
    display: flex;
    justify-content: space-between;
    width: min(100% - 24px, var(--sm-content));
  }
}
</style>
