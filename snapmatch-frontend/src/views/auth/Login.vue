<template>
  <AuthLayout>
    <section class="auth-card panel">
      <h1>欢迎登录</h1>
      <p>登录 SnapMatch，开始你的学习资料整理</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" class="soft-input" :prefix-icon="UserRound" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" class="soft-input" :prefix-icon="KeyRound" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <div class="form-row">
          <el-checkbox v-model="form.remember">记住登录状态</el-checkbox>
          <RouterLink to="/change-password">修改密码</RouterLink>
        </div>
        <el-button type="primary" native-type="submit" :loading="loading">登录</el-button>
      </el-form>
      <p class="center">还没有账号？<RouterLink to="/register">立即注册</RouterLink></p>
      <div class="quick-login">
        <span>演示账号</span>
        <button type="button" @click="quickLogin('user')">
          <small>普通用户</small>
          user / 123456
        </button>
        <button type="button" @click="quickLogin('admin')">
          <small>管理员</small>
          admin / 123456
        </button>
      </div>
    </section>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { KeyRound, UserRound } from 'lucide-vue-next'
import AuthLayout from '@/layouts/AuthLayout.vue'
import { useAuthStore } from '@/stores/authStore'
import { roleHome } from '@/utils/permission'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '', remember: true })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    const user = await auth.login(form)
    ElMessage.success(`欢迎回来，${user.nickname}`)
    router.push(route.query.redirect || roleHome(user.role))
  } finally {
    loading.value = false
  }
}

function quickLogin(username) {
  form.username = username
  form.password = '123456'
}
</script>

<style scoped>
.auth-card {
  width: 420px;
  padding: 34px;
}

h1 {
  margin: 0;
  font-size: 26px;
}

p {
  color: var(--sm-muted);
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: -6px 0 18px;
}

.el-button {
  width: 100%;
  height: 42px;
}

.center {
  text-align: center;
}

.quick-login {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 22px;
  padding-top: 20px;
  border-top: 1px solid var(--sm-border);
}

.quick-login > span {
  grid-column: 1 / -1;
  color: var(--sm-muted);
  font-size: 12px;
}

.quick-login button {
  padding: 10px 12px;
  border: 1px solid var(--sm-border);
  border-radius: 12px;
  background: #fff;
  color: var(--sm-text);
  text-align: left;
  cursor: pointer;
}

.quick-login button:hover {
  border-color: var(--sm-primary);
  background: rgba(238, 242, 255, 0.5);
}

.quick-login small {
  display: block;
  color: var(--sm-muted);
}

a {
  color: var(--sm-primary);
}

</style>
