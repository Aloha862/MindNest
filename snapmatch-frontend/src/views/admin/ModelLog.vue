<template>
  <main>
    <PageHeader title="模型日志" subtitle="OCR / VLM / OpenCV 处理记录" />
    <AdminTable :rows="rows" :loading="loading" :total="total" :page="page" :page-size="pageSize" placeholder="搜索模型名称或输入" @search="onSearch" @page-change="onPageChange">
      <template #filters>
        <el-select v-model="modelType" placeholder="全部类型" clearable @change="refresh"><el-option label="OpenCV" value="opencv" /><el-option label="YOLO" value="yolo" /><el-option label="OCR" value="ocr" /><el-option label="VLM" value="vlm" /><el-option label="System" value="system" /></el-select>
        <el-select v-model="stage" placeholder="全部阶段" clearable @change="refresh">
          <el-option label="预处理" value="preprocessing" />
          <el-option label="版面检测" value="yolo_running" />
          <el-option label="OCR" value="ocr_running" />
          <el-option label="公式识别" value="formula_running" />
          <el-option label="VLM" value="vlm_running" />
          <el-option label="结果校验" value="parsing" />
          <el-option label="写库" value="persisting" />
        </el-select>
        <el-select v-model="errorCode" placeholder="全部错误码" clearable @change="refresh">
          <el-option label="OCR_EMPTY" value="OCR_EMPTY" />
          <el-option label="OCR_LOW_CONFIDENCE" value="OCR_LOW_CONFIDENCE" />
          <el-option label="VLM_INVALID_JSON" value="VLM_INVALID_JSON" />
          <el-option label="VLM_EMPTY_RESULT" value="VLM_EMPTY_RESULT" />
          <el-option label="FORMULA_FAILED" value="FORMULA_FAILED" />
        </el-select>
        <el-select v-model="status" placeholder="全部状态" clearable @change="refresh"><el-option label="成功" value="success" /><el-option label="失败" value="failed" /></el-select>
      </template>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="类型"><template #default="{ row }"><StatusTag :status="row.status" :label="row.modelType" /></template></el-table-column>
      <el-table-column prop="modelName" label="模型" />
      <el-table-column prop="stage" label="阶段" />
      <el-table-column prop="errorCode" label="错误码"><template #default="{ row }">{{ row.errorCode || '—' }}</template></el-table-column>
      <el-table-column prop="taskId" label="关联任务" />
      <el-table-column prop="inputSummary" label="输入摘要" min-width="180" />
      <el-table-column prop="outputSummary" label="输出摘要" min-width="220" />
      <el-table-column label="耗时"><template #default="{ row }">{{ costText(row.costTime) }}</template></el-table-column>
      <el-table-column label="状态"><template #default="{ row }"><StatusTag :status="row.status" /></template></el-table-column>
      <el-table-column label="操作"><template #default="{ row }"><button class="icon-button" @click="open(row)"><View /></button></template></el-table-column>
    </AdminTable>
    <el-drawer v-model="drawer" title="日志详情" size="420px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="模型">{{ current.modelName }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ current.modelType }}</el-descriptions-item>
        <el-descriptions-item label="阶段">{{ current.stage || '—' }}</el-descriptions-item>
        <el-descriptions-item label="错误码">{{ current.errorCode || '—' }}</el-descriptions-item>
        <el-descriptions-item label="任务">{{ current.taskId || '—' }}</el-descriptions-item>
        <el-descriptions-item label="输入">{{ current.inputSummary }}</el-descriptions-item>
        <el-descriptions-item label="输出">{{ current.outputSummary }}</el-descriptions-item>
        <el-descriptions-item label="错误">{{ current.errorMessage || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { View } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import AdminTable from '@/components/admin/AdminTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { getModelLogs } from '@/api/admin'
import { costText } from '@/utils/format'

const rows = ref([])
const keyword = ref('')
const modelType = ref('')
const stage = ref('')
const errorCode = ref('')
const status = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)
const drawer = ref(false)
const current = ref(null)

async function load() {
  loading.value = true
  try {
    const res = await getModelLogs({ keyword: keyword.value, modelType: modelType.value, stage: stage.value, errorCode: errorCode.value, status: status.value, page: page.value, pageSize })
    rows.value = res.data.list || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}
function refresh() { page.value = 1; load() }
function onSearch(value) { keyword.value = value; refresh() }
function onPageChange(value) { page.value = value; load() }
function open(row) { current.value = row; drawer.value = true }
onMounted(load)
</script>
