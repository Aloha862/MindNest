<template>
  <main class="page-shell batch-page">
    <PageHeader title="批量联卷识别" :subtitle="batch ? `批次 ${batch.batchId}` : '正在加载批次进度'">
      <StatusTag v-if="batch" :status="batch.status" />
      <el-button v-if="batch?.status === 'completed'" type="primary" plain @click="exportBatch">导出整卷</el-button>
    </PageHeader>

    <section v-if="batch" class="panel progress-card">
      <div>
        <h2>{{ statusText }}</h2>
        <p>{{ batch.successCount }} 成功 · {{ batch.failedCount }} 失败 · {{ batch.questionCount }} 道题</p>
      </div>
      <el-progress :percentage="Number(batch.progress || 0)" :status="batch.failedCount ? 'warning' : undefined" />
    </section>

    <el-alert v-if="networkFailures >= 3" class="network-alert" type="warning" :closable="false" title="网络不稳定，后台任务仍会继续执行" />

    <section class="panel task-list">
      <header>
        <h3>图片任务</h3>
        <span>{{ batch?.taskCount || 0 }} 个任务</span>
      </header>
      <el-skeleton v-if="loading && !batch" :rows="6" animated />
      <el-table v-else :data="batch?.tasks || []" style="width: 100%">
        <el-table-column prop="batchOrder" label="#" width="70" />
        <el-table-column prop="fileName" label="文件" min-width="180" />
        <el-table-column prop="currentStep" label="阶段" min-width="180" />
        <el-table-column label="进度" width="180">
          <template #default="{ row }"><el-progress :percentage="row.progress || 0" /></template>
        </el-table-column>
        <el-table-column label="状态" width="130">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="错误" min-width="150">
          <template #default="{ row }">{{ row.errorCode || '无' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="$router.push(`/user/recognition/${row.id}`)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { getRecognitionBatch } from '@/api/recognition'
import { exportQuestions } from '@/api/export'

const route = useRoute()
const batch = ref(null)
const loading = ref(false)
const networkFailures = ref(0)
let timer = null

const statusText = computed(() => {
  if (!batch.value) return ''
  if (batch.value.status === 'completed') return '整批识别完成'
  if (batch.value.status === 'failed') return '整批识别失败'
  return '批量识别处理中'
})

function isDone(status) {
  return ['completed', 'failed'].includes(status)
}

async function load() {
  loading.value = true
  try {
    batch.value = (await getRecognitionBatch(route.params.batchId)).data
    networkFailures.value = 0
    if (isDone(batch.value.status) && timer) {
      window.clearInterval(timer)
      timer = null
    }
  } catch (error) {
    networkFailures.value += 1
    if (networkFailures.value >= 3) ElMessage.warning('网络不稳定，稍后将继续尝试刷新')
  } finally {
    loading.value = false
  }
}

async function exportBatch() {
  await exportQuestions({ range: 'batch', batchId: route.params.batchId, format: 'markdown' })
  ElMessage.success('整批导出已生成')
}

onMounted(async () => {
  await load()
  timer = window.setInterval(load, 1500)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>

<style scoped>
.progress-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 360px);
  gap: 24px;
  align-items: center;
  margin-bottom: 18px;
  padding: 20px;
}

.progress-card h2,
.task-list h3 {
  margin: 0 0 6px;
}

.progress-card p,
.task-list span {
  margin: 0;
  color: var(--sm-muted);
}

.network-alert {
  margin-bottom: 18px;
}

.task-list {
  padding: 20px;
}

.task-list header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 14px;
}

@media (max-width: 900px) {
  .progress-card {
    grid-template-columns: 1fr;
  }
}
</style>
