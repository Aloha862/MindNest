<template>
  <AuthLayout>
    <section class="auth-card panel">
      <h1>修改密码</h1>
      <p>请在已登录状态下提交，密码会同步更新到后端数据库</p>
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="原密码" prop="oldPassword">
          <el-input v-model="form.oldPassword" class="soft-input" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="form.newPassword" class="soft-input" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" class="soft-input" type="password" show-password />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading">提交</el-button>
      </el-form>
    </section>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AuthLayout from '@/layouts/AuthLayout.vue'
import { changePassword } from '@/api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const rules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, min: 6, message: '新密码至少 6 位', trigger: 'blur' }],
  confirmPassword: [{
    validator: (_, value, cb) => value === form.newPassword ? cb() : cb(new Error('两次输入的新密码不一致')),
    trigger: 'blur'
  }]
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await changePassword(form)
    ElMessage.success('密码修改成功，请重新登录')
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
</style>
