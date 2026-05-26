<template>
  <main class="page-shell result-page">
    <PageHeader title="识别结果" subtitle="从图片上传到结构化题目卡片的完整处理过程">
      <StatusTag v-if="task" :status="task.status" />
    </PageHeader>

    <section v-if="task" class="progress-card panel">
      <div>
        <h2>{{ task.currentStep || '识别任务处理中' }}</h2>
        <p>{{ task.fileName || `任务 #${task.id}` }}</p>
        <el-alert
          v-if="task.errorCode"
          class="task-alert"
          type="error"
          :closable="false"
          :title="errorTitle"
          show-icon
        >
          <div class="error-actions">
            <span>{{ task.errorMessage || '请点击重新识别，或到管理端诊断查看阶段日志。' }}</span>
            <el-button size="small" type="danger" plain :loading="retrying" @click="retryCurrentTask">
              重新识别
            </el-button>
          </div>
        </el-alert>
      </div>
      <el-progress
        :percentage="Number(task.progress || 0)"
        :status="task.status === 'failed' ? 'exception' : task.status === 'needs_review' ? 'warning' : undefined"
      />
    </section>

    <section v-if="loading" class="panel loading-card">
      <el-skeleton :rows="6" animated />
    </section>

    <section v-else-if="task" class="result-grid">
      <div class="left">
        <section class="panel image-card">
          <header>
            <h3>原图与预处理图</h3>
            <span>{{ file?.fileName || task.fileName }}</span>
          </header>
          <div class="images">
            <figure>
              <img :src="file?.originalImageUrl || ocr.originalImageUrl" alt="原图" />
              <figcaption>原始图片</figcaption>
            </figure>
            <figure>
              <img :src="processedImageUrl" alt="预处理图" />
              <figcaption>{{ processedReady ? '预处理结果' : '等待 OpenCV 预处理' }}</figcaption>
            </figure>
          </div>
        </section>

        <VisualDetectionPanel
          v-if="showYoloPanel"
          :image-url="file?.originalImageUrl || ocr.originalImageUrl"
          :yolo="ocr.yolo"
          :pending="!yoloReady"
        />
        <OCRResultPanel v-if="showOcrPanel" :result="ocr" :pending="!ocrReady" />
        <VLMResultPanel v-if="showVlmPanel" :result="vlm" :pending="!vlmReady" />
      </div>

      <aside>
        <ProcessTimeline :status="task.status" />
        <section class="panel generated">
          <header>
            <h3>生成题目卡片</h3>
            <span>{{ vlm.questions.length }} 张</span>
          </header>
          <template v-if="vlmReady">
            <QuestionCard
              v-for="item in vlm.questions"
              :key="item.id || item.title"
              :question="item"
              :deletable="false"
              :wrongable="!!item.id"
              @wrong="addWrong"
            />
            <el-empty v-if="!vlm.questions.length" description="暂无生成题目" />
          </template>
          <el-skeleton v-else :rows="4" animated />
        </section>
      </aside>
    </section>

    <el-empty v-else description="未找到识别任务" />
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import OCRResultPanel from '@/components/recognition/OCRResultPanel.vue'
import VisualDetectionPanel from '@/components/recognition/VisualDetectionPanel.vue'
import VLMResultPanel from '@/components/recognition/VLMResultPanel.vue'
import ProcessTimeline from '@/components/recognition/ProcessTimeline.vue'
import QuestionCard from '@/components/question/QuestionCard.vue'
import { getFileDetail } from '@/api/file'
import { getOCRResult, getTaskDetail, getTaskProgress, getVLMResult, retryTask } from '@/api/recognition'
import { markQuestionWrong } from '@/api/question'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const retrying = ref(false)
const task = ref(null)
const file = ref(null)
const ocr = reactive({
  rawText: '',
  blocks: [],
  formulaBlocks: [],
  sections: [],
  layoutBlocks: [],
  yolo: {},
  originalImageUrl: '',
  preprocessImageUrl: ''
})
const vlm = reactive({ summary: '', layoutType: '', materialType: '', questions: [] })
let timer = null

const order = ['pending', 'preprocessing', 'yolo_running', 'ocr_running', 'formula_running', 'vlm_running', 'parsing', 'persisting', 'completed', 'needs_review', 'failed']
const statusIndex = computed(() => Math.max(order.indexOf(task.value?.status || 'pending'), 0))
const processedReady = computed(() => Boolean(file.value?.preprocessImageUrl || ocr.preprocessImageUrl))
const processedImageUrl = computed(() => file.value?.preprocessImageUrl || ocr.preprocessImageUrl || file.value?.originalImageUrl || ocr.originalImageUrl)
const yoloReady = computed(() => Boolean(ocr.yolo?.detections?.length || ocr.yolo?.mode))
const ocrReady = computed(() => Boolean(ocr.rawText || ocr.blocks?.length || ocr.formulaBlocks?.length))
const vlmReady = computed(() => Boolean(vlm.summary || vlm.questions.length))
const showYoloPanel = computed(() => statusIndex.value >= 2 || yoloReady.value)
const showOcrPanel = computed(() => statusIndex.value >= 3 || ocrReady.value)
const showVlmPanel = computed(() => statusIndex.value >= 4 || vlmReady.value)
const errorTitle = computed(() => `${task.value?.errorStage || 'pipeline'}: ${task.value?.errorCode || 'UNKNOWN_ERROR'}`)

function isDone(status) {
  return ['completed', 'needs_review', 'failed'].includes(status)
}

async function refreshSnapshot() {
  const taskId = route.params.taskId
  task.value = (await getTaskDetail(taskId)).data
  if (task.value?.fileId) {
    file.value = (await getFileDetail(task.value.fileId)).data
  }

  if (statusIndex.value >= 2 || yoloReady.value || ocrReady.value) {
    Object.assign(ocr, (await getOCRResult(taskId)).data || {})
  }

  if (statusIndex.value >= 4 || vlmReady.value) {
    Object.assign(vlm, { summary: '', layoutType: '', materialType: '', questions: [] }, (await getVLMResult(taskId)).data || {})
  }
}

async function addWrong(question) {
  await markQuestionWrong(question.id, { source: '识别结果页' })
  question.isWrong = true
  ElMessage.success('已加入错题本')
}

async function retryCurrentTask() {
  if (!task.value?.id || retrying.value) return
  retrying.value = true
  try {
    const { data } = await retryTask(task.value.id)
    const nextTaskId = data?.task?.id
    ElMessage.success('已创建重新识别任务')
    if (nextTaskId) {
      router.push(`/user/recognition/${nextTaskId}`)
    }
  } finally {
    retrying.value = false
  }
}

function startPolling() {
  if (timer || !task.value || isDone(task.value.status)) return
  timer = window.setInterval(async () => {
    const progress = (await getTaskProgress(route.params.taskId)).data
    const previousStatus = task.value?.status
    task.value = { ...task.value, ...progress }
    if (previousStatus !== progress.status || isDone(progress.status)) {
      await refreshSnapshot()
    }
    if (isDone(task.value?.status)) {
      window.clearInterval(timer)
      timer = null
      await refreshSnapshot()
    }
  }, 1500)
}

onMounted(async () => {
  try {
    await refreshSnapshot()
    startPolling()
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.result-page {
  padding-bottom: 80px;
}

.progress-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 360px);
  gap: 24px;
  align-items: center;
  margin-bottom: 18px;
  padding: 20px;
}

.progress-card h2 {
  margin: 0 0 6px;
  font-size: 18px;
}

.progress-card p {
  margin: 0;
  color: var(--sm-muted);
}

.task-alert {
  margin-top: 10px;
}

.error-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.error-actions span {
  line-height: 1.6;
  word-break: break-word;
}

.loading-card {
  padding: 24px;
}

.result-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.9fr;
  gap: 18px;
}

.left,
aside {
  display: grid;
  gap: 18px;
  align-content: start;
}

.image-card {
  padding: 22px;
}

.image-card header,
.generated header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 16px;
}

h3 {
  margin: 0;
}

.image-card header span,
.generated header span {
  color: var(--sm-muted);
  font-size: 13px;
}

.images {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

figure {
  margin: 0;
}

.image-card img {
  width: 100%;
  height: 240px;
  object-fit: contain;
  border-radius: 14px;
  background: rgba(238, 242, 255, 0.45);
}

figcaption {
  margin-top: 8px;
  color: var(--sm-muted);
  font-size: 12px;
  text-align: center;
}

.generated {
  display: grid;
  gap: 12px;
  padding: 20px;
}

@media (max-width: 960px) {
  .progress-card,
  .result-grid,
  .images {
    grid-template-columns: 1fr;
  }

  .error-actions {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
