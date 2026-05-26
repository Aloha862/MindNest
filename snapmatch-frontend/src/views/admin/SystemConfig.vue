<template>
  <main>
    <PageHeader title="系统配置" subtitle="模型服务、上传限制与功能开关" />
    <section v-loading="loading" class="config-grid">
      <section class="panel config-card">
        <h3>功能开关</h3>
        <label>启用 OCR 文字识别<small>关闭后将仅使用 VLM 直接分析</small><el-switch v-model="config.ocrEnabled" /></label>
        <label>启用 VLM 视觉语言模型<small>关闭后将仅生成 OCR 文本</small><el-switch v-model="config.vlmEnabled" /></label>
        <label>连接真实后端<small>登录和业务数据均来自后端数据库</small><el-switch v-model="config.backendEnabled" disabled /></label>
      </section>
      <section class="panel config-card">
        <h3>上传与模型服务</h3>
        <el-form label-position="top">
          <el-form-item label="默认上传大小限制（MB）"><el-input-number v-model="config.maxUploadSizeMb" :min="1" :max="100" controls-position="right" style="width: 100%" /></el-form-item>
          <el-form-item label="支持文件类型"><el-input class="soft-input" v-model="config.allowedFileTypes" /></el-form-item>
          <el-form-item label="模型服务地址"><el-input class="soft-input" v-model="config.modelEndpoint" /></el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
        </el-form>
      </section>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { getSystemConfig, updateSystemConfig } from '@/api/admin'

const loading = ref(false)
const saving = ref(false)
const config = reactive({
  ocrEnabled: true,
  vlmEnabled: true,
  backendEnabled: true,
  maxUploadSizeMb: 10,
  allowedFileTypes: 'jpg, jpeg, png',
  modelEndpoint: 'http://127.0.0.1:8000/api'
})

async function load() {
  loading.value = true
  try {
    Object.assign(config, (await getSystemConfig()).data)
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    Object.assign(config, (await updateSystemConfig(config)).data)
    ElMessage.success('配置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.config-card {
  padding: 22px;
}

.config-card h3 {
  margin: 0 0 20px;
}

label {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 16px;
  margin: 20px 0;
}

small {
  color: var(--sm-muted);
}

@media (max-width: 900px) {
  .config-grid {
    grid-template-columns: 1fr;
  }
}
</style>
