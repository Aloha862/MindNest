<template>
  <main class="page-shell">
    <PageHeader title="个人中心" subtitle="管理你的账号资料和登录状态" />
    <section class="panel profile">
      <div class="avatar">{{ avatarText }}</div>
      <el-form label-position="top">
        <el-form-item label="用户名"><el-input class="soft-input" :model-value="auth.userInfo?.username" /></el-form-item>
        <el-form-item label="昵称"><el-input class="soft-input" :model-value="auth.userInfo?.nickname" /></el-form-item>
        <el-form-item label="手机号"><el-input class="soft-input" :model-value="auth.userInfo?.phone" /></el-form-item>
        <el-button type="primary">保存资料</el-button>
        <el-button @click="$router.push('/change-password')">修改密码</el-button>
        <el-button type="danger" plain @click="logout">退出登录</el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()
const router = useRouter()
const avatarText = computed(() => {
  const nickname = auth.userInfo?.nickname?.trim()
  const username = auth.userInfo?.username?.trim()
  const source = nickname || username || '用'
  return source.slice(0, 1).toUpperCase()
})
async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.profile {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 28px;
  max-width: 720px;
  padding: 28px;
}

.avatar {
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  border-radius: 28px;
  color: #fff;
  background: linear-gradient(135deg, var(--sm-primary), var(--sm-ai));
  font-size: 34px;
  font-weight: 850;
}

@media (max-width: 700px) {
  .profile {
    grid-template-columns: 1fr;
  }
}
</style>
