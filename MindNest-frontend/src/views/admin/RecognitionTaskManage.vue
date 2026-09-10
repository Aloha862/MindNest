<template>
  <main>
    <PageHeader title="识别任务管理" :subtitle="`共 ${total} 条任务`" />
    <AdminTable :rows="rows" :loading="loading" :total="total" :page="page" :page-size="pageSize" placeholder="搜索文件名、阶段或错误码" @search="onSearch" @page-change="onPageChange">
      <template #filters>
        <el-select v-model="status" placeholder="全部状态" clearable @change="refresh">
          <el-option label="已完成" value="completed" />
          <el-option label="待复核" value="needs_review" />
          <el-option label="失败" value="failed" />
          <el-option label="处理中" value="vlm_running" />
          <el-option label="等待处理" value="pending" />
        </el-select>
      </template>
      <el-table-column prop="id" label="任务 ID" width="100" />
      <el-table-column prop="fileName" label="文件名" min-width="180" />
      <el-table-column prop="userName" label="用户" width="130" />
      <el-table-column prop="batchId" label="批次" min-width="150">
        <template #default="{ row }">{{ row.batchId || '单图' }}</template>
      </el-table-column>
      <el-table-column prop="currentStep" label="当前阶段" min-width="180" />
      <el-table-column prop="errorCode" label="错误码" min-width="150">
        <template #default="{ row }">{{ row.errorCode || '无' }}</template>
      </el-table-column>
      <el-table-column prop="errorStage" label="失败阶段" width="120">
        <template #default="{ row }">{{ row.errorStage || '无' }}</template>
      </el-table-column>
      <el-table-column label="进度" width="150"><template #default="{ row }"><el-progress :percentage="row.progress || 0" /></template></el-table-column>
      <el-table-column label="状态" width="140"><template #default="{ row }"><StatusTag :status="row.status" /></template></el-table-column>
      <el-table-column label="耗时" width="130">
        <template #default="{ row }">{{ durationText(row) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <div class="table-actions">
            <el-button size="small" link type="primary" @click="openDiagnostics(row)">诊断</el-button>
            <el-button size="small" link @click="$router.push(`/admin/tasks/${row.id}`)">详情</el-button>
            <el-button size="small" link type="warning" :disabled="row.status !== 'failed'" @click="retry(row)">重试</el-button>
          </div>
        </template>
      </el-table-column>
    </AdminTable>

    <el-drawer v-model="diagnosticsVisible" title="任务诊断" size="620px">
      <el-skeleton v-if="diagnosticsLoading" :rows="8" animated />
      <template v-else-if="diagnostics">
        <section class="diagnostic-block">
          <h3>概览</h3>
          <p><span>任务</span>#{{ diagnostics.task?.id }} · {{ diagnostics.task?.fileName }}</p>
          <p><span>状态</span><StatusTag :status="diagnostics.task?.status" /></p>
          <p><span>错误</span>{{ diagnostics.errorStage || '无' }} / {{ diagnostics.errorCode || '无' }}</p>
        </section>
        <section class="diagnostic-block">
          <h3>图像质量</h3>
          <div class="quality-grid">
            <p v-for="(value, key) in diagnostics.quality || {}" :key="key"><span>{{ key }}</span>{{ Array.isArray(value) ? value.join('；') : value }}</p>
          </div>
        </section>
        <section class="diagnostic-block">
          <h3>阶段耗时</h3>
          <p v-for="(value, key) in diagnostics.stageCosts || {}" :key="key"><span>{{ key }}</span>{{ value }} ms</p>
        </section>
        <section class="diagnostic-block">
          <h3>模型日志</h3>
          <el-timeline>
            <el-timeline-item v-for="log in diagnostics.logs || []" :key="log.id" :type="log.status === 'failed' ? 'danger' : 'success'" :timestamp="`${log.stage || log.modelType} · ${log.costTime || 0}ms`">
              <strong>{{ log.modelName }}</strong>
              <p>{{ log.outputSummary || log.errorMessage || '无摘要' }}</p>
              <el-tag v-if="log.errorCode" type="danger" size="small">{{ log.errorCode }}</el-tag>
            </el-timeline-item>
          </el-timeline>
        </section>
      </template>
    </el-drawer>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import AdminTable from '@/components/admin/AdminTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { getAdminTasks } from '@/api/admin'
import { getTaskDiagnostics, retryTask } from '@/api/recognition'

const rows = ref([])
const keyword = ref('')
const status = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)
const diagnosticsVisible = ref(false)
const diagnosticsLoading = ref(false)
const diagnostics = ref(null)

function durationText(row) {
  if (!row.startedAt || !row.finishedAt) return '未完成'
  const start = new Date(row.startedAt).getTime()
  const end = new Date(row.finishedAt).getTime()
  if (!start || !end) return '未知'
  return `${Math.max(0, Math.round((end - start) / 1000))}s`
}

async function load() {
  loading.value = true
  try {
    const res = await getAdminTasks({ keyword: keyword.value, status: status.value, page: page.value, pageSize })
    rows.value = res.data.list || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function refresh() {
  page.value = 1
  load()
}

function onSearch(value) {
  keyword.value = value
  refresh()
}

function onPageChange(value) {
  page.value = value
  load()
}

async function openDiagnostics(row) {
  diagnosticsVisible.value = true
  diagnosticsLoading.value = true
  try {
    diagnostics.value = (await getTaskDiagnostics(row.id)).data
  } finally {
    diagnosticsLoading.value = false
  }
}

async function retry(row) {
  if (row.status !== 'failed') return
  await retryTask(row.id)
  ElMessage.success('识别任务已重新提交')
  load()
}

onMounted(load)
</script>

<style scoped>
.diagnostic-block {
  padding: 14px 0;
  border-bottom: 1px solid var(--sm-border);
}

.diagnostic-block h3 {
  margin: 0 0 12px;
}

.diagnostic-block p {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.diagnostic-block span {
  color: var(--sm-muted);
}

.quality-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 14px;
}

.quality-grid p {
  margin: 0;
}
</style>
