<template>
  <main class="page-shell">
    <PageHeader title="识别记录" subtitle="查看和管理你的所有上传和识别任务" />
    <AdminTable
      :rows="rows"
      :loading="loading"
      :total="total"
      :page="page"
      :page-size="pageSize"
      placeholder="搜索文件名"
      @search="onSearch"
      @page-change="onPageChange"
    >
      <template #filters>
        <el-select v-model="status" placeholder="全部状态" clearable @change="refresh">
          <el-option label="已完成" value="completed" />
          <el-option label="VLM 分析中" value="vlm_running" />
          <el-option label="YOLO 检测中" value="yolo_running" />
          <el-option label="等待处理" value="pending" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-button @click="reset">重置</el-button>
      </template>
      <el-table-column prop="id" label="任务编号" width="110" />
      <el-table-column prop="fileName" label="文件名称" min-width="180" />
      <el-table-column label="上传时间" width="190"><template #default="{ row }">{{ safeDate(row.createdAt) }}</template></el-table-column>
      <el-table-column label="当前状态" width="150"><template #default="{ row }"><StatusTag :status="row.status" /></template></el-table-column>
      <el-table-column prop="progress" label="进度" width="90"><template #default="{ row }">{{ row.progress }}%</template></el-table-column>
      <el-table-column prop="questionCount" label="题目数" width="90" />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <div class="table-actions">
            <button class="icon-button" @click="$router.push(`/user/recognition/${row.id}`)"><View /></button>
            <button class="icon-button" @click="load"><Refresh /></button>
          </div>
        </template>
      </el-table-column>
    </AdminTable>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Refresh, View } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import AdminTable from '@/components/admin/AdminTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { getTasks } from '@/api/recognition'
import { safeDate } from '@/utils/format'

const rows = ref([])
const keyword = ref('')
const status = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getTasks({ keyword: keyword.value, status: status.value, page: page.value, pageSize })
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
function reset() {
  keyword.value = ''
  status.value = ''
  refresh()
}
function onSearch(value) {
  keyword.value = value
  refresh()
}
function onPageChange(value) {
  page.value = value
  load()
}
onMounted(load)
</script>
