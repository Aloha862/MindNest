<template>
  <AuthLayout>
    <section class="auth-card panel">
      <h1>创建账号</h1>
      <p>加入 SnapMatch，让你的错题真正可复用</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="用户名" prop="username"><el-input v-model="form.username" class="soft-input" placeholder="字母/数字组合" /></el-form-item>
        <el-form-item label="昵称" prop="nickname"><el-input v-model="form.nickname" class="soft-input" placeholder="用于展示" /></el-form-item>
        <el-form-item label="手机号" prop="phone"><el-input v-model="form.phone" class="soft-input" placeholder="用于找回账号" /></el-form-item>
        <el-form-item label="密码" prop="password"><el-input v-model="form.password" class="soft-input" type="password" placeholder="至少 6 位" /></el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword"><el-input v-model="form.confirmPassword" class="soft-input" type="password" placeholder="再次输入密码" /></el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading">注册</el-button>
      </el-form>
      <p class="center">已有账号？<RouterLink to="/login">返回登录</RouterLink></p>
    </section>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AuthLayout from '@/layouts/AuthLayout.vue'
import { register } from '@/api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', nickname: '', phone: '', password: '', confirmPassword: '', role: 'user' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  phone: [{ pattern: /^1\d{10}$/, message: '请输入正确手机号', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  confirmPassword: [{ validator: (_, value, cb) => value === form.password ? cb() : cb(new Error('两次密码不一致')), trigger: 'blur' }]
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await register(form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-card {
  width: 420px;
  padding: 32px;
}

h1 {
  margin: 0;
  font-size: 26px;
}

p {
  color: var(--sm-muted);
}

.el-button {
  width: 100%;
  height: 42px;
}

.center {
  text-align: center;
}

a {
  color: var(--sm-primary);
}
</style>
