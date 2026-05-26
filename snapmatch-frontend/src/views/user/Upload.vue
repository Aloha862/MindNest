<template>
  <main class="page-shell upload-page">
    <PageHeader title="上传识别" subtitle="支持单图识别和批量联卷，后台会异步执行 OCR、公式识别和 VLM 解析" />
    <section class="upload-grid">
      <div>
        <ImageUploader :previews="previews" multiple @select="onSelect" />
        <section class="panel options">
          <h3>识别选项</h3>
          <label><Camera />图像预处理<small>去噪、增强、透视校正</small><el-switch v-model="options.preprocess" /></label>
          <label><ScanSearch />版面检测<small>题干、公式、解析区域</small><el-switch v-model="options.yolo" /></label>
          <label><ScanLine />OCR 文字识别<small>提取题目原文</small><el-switch v-model="options.ocr" /></label>
          <label><Sparkles />VLM 智能解析<small>生成结构化题卡</small><el-switch v-model="options.vlm" /></label>
        </section>
      </div>
      <aside>
        <UploadPreview :files="queue" removable @remove="removeFile" />
        <section class="panel side-form">
          <h3>科目提示</h3>
          <el-select v-model="form.subjectHint" class="soft-input" style="width: 100%">
            <el-option v-for="item in subjects" :key="item" :label="item" :value="item" />
          </el-select>
          <h3>资料类型</h3>
          <el-select v-model="form.fileType" class="soft-input" style="width: 100%">
            <el-option label="作业" value="homework" />
            <el-option label="试卷" value="exam" />
            <el-option label="错题" value="mistake" />
            <el-option label="课堂笔记" value="note" />
          </el-select>
          <h3>备注</h3>
          <el-input v-model="form.remark" class="soft-input" type="textarea" :rows="3" placeholder="例如：第三章月考第二大题" />
          <p class="policy">支持 {{ policy.allowedFileTypes }}，单文件不超过 {{ policy.maxUploadSizeMb }}MB</p>
        </section>
        <UploadTips />
        <el-button type="primary" size="large" :disabled="!queue.length || loading" :loading="loading" @click="submit">
          {{ queue.length > 1 ? '批量上传并识别' : '开始识别' }}
        </el-button>
      </aside>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Camera, ScanLine, ScanSearch, Sparkles } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import ImageUploader from '@/components/upload/ImageUploader.vue'
import UploadPreview from '@/components/upload/UploadPreview.vue'
import UploadTips from '@/components/upload/UploadTips.vue'
import { getUploadPolicy, uploadBatchFiles, uploadFile } from '@/api/file'
import { batchStartRecognition, startRecognition } from '@/api/recognition'

const router = useRouter()
const queue = ref([])
const loading = ref(false)
const subjects = ['数学', '英语', '计算机', '政治', '专业课', '物理', '其他']
const policy = reactive({ allowedFileTypes: 'jpg, jpeg, png', maxUploadSizeMb: 10 })
const options = reactive({ preprocess: true, yolo: true, ocr: true, vlm: true })
const form = reactive({ subjectHint: '数学', fileType: 'homework', remark: '' })

const previews = computed(() => queue.value.map((item) => item.previewUrl).filter(Boolean))

function isValid(file) {
  const allowed = policy.allowedFileTypes.split(',').map((item) => item.trim().toLowerCase().replace(/^\./, '')).filter(Boolean)
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (allowed.length && !allowed.includes(ext)) {
    ElMessage.error(`仅支持 ${policy.allowedFileTypes} 文件`)
    return false
  }
  if (file.size > policy.maxUploadSizeMb * 1024 * 1024) {
    ElMessage.error(`文件大小不能超过 ${policy.maxUploadSizeMb}MB`)
    return false
  }
  return true
}

function onSelect(selected) {
  const files = Array.isArray(selected) ? selected : [selected]
  const next = files.filter(Boolean).filter(isValid).map((file) => ({
    raw: file,
    name: file.name,
    size: file.size,
    type: file.type,
    status: 'local',
    previewUrl: URL.createObjectURL(file)
  }))
  queue.value = [...queue.value, ...next]
}

function removeFile(index) {
  const [item] = queue.value.splice(index, 1)
  if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl)
}

function recognitionPayload(fileIds) {
  return {
    fileIds,
    enablePreprocess: options.preprocess,
    enableYOLO: options.yolo,
    enableOCR: options.ocr,
    enableVLM: options.vlm
  }
}

async function submit() {
  if (!queue.value.length || loading.value) return
  loading.value = true
  try {
    queue.value.forEach((item) => { item.status = 'uploading' })
    if (queue.value.length === 1) {
      const item = queue.value[0]
      const uploaded = await uploadFile({
        file: item.raw,
        remark: form.remark,
        subjectHint: form.subjectHint,
        fileType: form.fileType
      })
      item.status = 'uploaded'
      const task = await startRecognition({
        fileId: uploaded.data.id,
        enablePreprocess: options.preprocess,
        enableYOLO: options.yolo,
        enableOCR: options.ocr,
        enableVLM: options.vlm
      })
      router.push(`/user/recognition/${task.data.id}`)
      return
    }
    const uploaded = await uploadBatchFiles({
      files: queue.value.map((item) => item.raw),
      remark: form.remark,
      subjectHint: form.subjectHint,
      fileType: form.fileType
    })
    const fileIds = (uploaded.data.success || []).map((item) => item.id)
    if (!fileIds.length) throw new Error('没有文件上传成功')
    queue.value.forEach((item) => { item.status = 'uploaded' })
    const started = await batchStartRecognition(recognitionPayload(fileIds))
    router.push(`/user/recognition/batches/${started.data.batchId || uploaded.data.batchId}`)
  } catch (error) {
    queue.value.forEach((item) => { if (item.status === 'uploading') item.status = 'failed' })
    ElMessage.error(error?.message || '上传或识别启动失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    Object.assign(policy, (await getUploadPolicy()).data)
  } catch {
    // 保留默认上传策略。
  }
})

onUnmounted(() => {
  queue.value.forEach((item) => item.previewUrl && URL.revokeObjectURL(item.previewUrl))
})
</script>

<style scoped>
.upload-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 24px;
}

.options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 18px;
  padding: 18px;
}

.options h3 {
  grid-column: 1 / -1;
  margin: 0;
}

.options label {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 14px;
  border: 1px solid var(--sm-border);
  border-radius: 12px;
}

small {
  display: block;
  color: var(--sm-muted);
}

aside {
  display: grid;
  gap: 18px;
  align-content: start;
}

.side-form {
  padding: 20px;
}

.side-form h3 {
  margin: 18px 0 8px;
}

.side-form h3:first-child {
  margin-top: 0;
}

.policy {
  margin: 12px 0 0;
  color: var(--sm-muted);
  font-size: 13px;
}

aside > .el-button {
  height: 42px;
}

@media (max-width: 960px) {
  .upload-grid,
  .options {
    grid-template-columns: 1fr;
  }
}
</style>
