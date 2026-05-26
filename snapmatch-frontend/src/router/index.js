import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { roleHome } from '@/utils/permission'

const routes = [
  { path: '/', component: () => import('@/views/public/Landing.vue'), meta: { public: true } },
  { path: '/about', component: () => import('@/views/public/About.vue'), meta: { public: true } },
  { path: '/login', component: () => import('@/views/auth/Login.vue'), meta: { public: true, authPage: true } },
  { path: '/register', component: () => import('@/views/auth/Register.vue'), meta: { public: true, authPage: true } },
  { path: '/change-password', component: () => import('@/views/auth/ChangePassword.vue'), meta: { public: true, authPage: true } },
  {
    path: '/user',
    component: () => import('@/layouts/UserLayout.vue'),
    meta: { requiresAuth: true, role: 'user' },
    children: [
      { path: '', redirect: '/user/dashboard' },
      { path: 'dashboard', component: () => import('@/views/user/Dashboard.vue') },
      { path: 'upload', component: () => import('@/views/user/Upload.vue') },
      { path: 'recognition/batches/:batchId', component: () => import('@/views/user/RecognitionBatchResult.vue') },
      { path: 'recognition/:taskId', component: () => import('@/views/user/RecognitionResult.vue') },
      { path: 'history', component: () => import('@/views/user/RecognitionHistory.vue') },
      { path: 'questions', component: () => import('@/views/user/QuestionList.vue') },
      { path: 'questions/:id', component: () => import('@/views/user/QuestionDetail.vue') },
      { path: 'subjects', component: () => import('@/views/user/SubjectCenter.vue') },
      { path: 'wrong-questions', component: () => import('@/views/user/WrongQuestions.vue') },
      { path: 'export', component: () => import('@/views/user/ExportCenter.vue') },
      { path: 'profile', component: () => import('@/views/user/Profile.vue') }
    ]
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', component: () => import('@/views/admin/AdminDashboard.vue') },
      { path: 'users', component: () => import('@/views/admin/UserManage.vue') },
      { path: 'files', component: () => import('@/views/admin/FileManage.vue') },
      { path: 'tasks', component: () => import('@/views/admin/RecognitionTaskManage.vue') },
      { path: 'tasks/:taskId', component: () => import('@/views/user/RecognitionResult.vue') },
      { path: 'questions', component: () => import('@/views/admin/QuestionManage.vue') },
      { path: 'questions/:id', component: () => import('@/views/user/QuestionDetail.vue') },
      { path: 'model-logs', component: () => import('@/views/admin/ModelLog.vue') },
      { path: 'system-config', component: () => import('@/views/admin/SystemConfig.vue') }
    ]
  },
  { path: '/403', component: () => import('@/views/error/Forbidden.vue'), meta: { public: true } },
  { path: '/404', component: () => import('@/views/error/NotFound.vue'), meta: { public: true } },
  { path: '/:pathMatch(.*)*', redirect: '/404' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.path === '/' && auth.isLogin) return roleHome(auth.role)
  if (to.meta.authPage && auth.isLogin) return roleHome(auth.role)
  if (to.meta.requiresAuth && !auth.isLogin) return `/login?redirect=${encodeURIComponent(to.fullPath)}`
  if (to.path.startsWith('/admin') && auth.role !== 'admin') return '/403'
  return true
})

export default router
