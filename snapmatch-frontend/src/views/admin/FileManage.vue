<template>
  <main>
    <PageHeader title="文件管理" :subtitle="`共 ${total} 个文件`" />
    <AdminTable :rows="rows" :loading="loading" :total="total" :page="page" :page-size="pageSize" placeholder="搜索文件名" @search="onSearch" @page-change="onPageChange">
      <template #filters>
        <el-select v-model="status" placeholder="全部状态" clearable @change="refresh"><el-option label="已识别" value="recognized" /><el-option label="处理中" value="processing" /><el-option label="失败" value="failed" /><el-option label="已上传" value="uploaded" /></el-select>
        <el-select v-model="fileType" placeholder="全部类型" clearable @change="refresh"><el-option label="作业" value="homework" /><el-option label="错题" value="mistake" /></el-select>
      </template>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="缩略图" width="120"><template #default="{ row }"><img class="thumb" :src="row.originalImageUrl" alt="" /></template></el-table-column>
      <el-table-column prop="fileName" label="文件名" min-width="180" />
      <el-table-column prop="userName" label="上传用户" />
      <el-table-column label="大小"><template #default="{ row }">{{ formatFileSize(row.size) }}</template></el-table-column>
      <el-table-column label="状态"><template #default="{ row }"><StatusTag :status="row.status" /></template></el-table-column>
      <el-table-column prop="createdAt" label="上传时间" width="190" />
      <el-table-column label="操作" width="110">
        <template #default="{ row }">
          <div class="table-actions"><button class="icon-button" @click="open(row)"><View /></button><button class="icon-button danger" @click="remove(row)"><Delete /></button></div>
        </template>
      </el-table-column>
    </AdminTable>
    <el-drawer v-model="drawer" title="文件详情" size="420px">
      <img v-if="current?.originalImageUrl" class="preview-img" :src="current.originalImageUrl" alt="" />
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="文件名">{{ current.fileName }}</el-descriptions-item>
        <el-descriptions-item label="上传用户">{{ current.userName }}</el-descriptions-item>
        <el-descriptions-item label="大小">{{ formatFileSize(current.size) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ current.status }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, View } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import AdminTable from '@/components/admin/AdminTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { deleteAdminFile, getAdminFiles } from '@/api/admin'
import { formatFileSize } from '@/utils/format'

const rows = ref([])
const keyword = ref('')
const status = ref('')
const fileType = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)
const drawer = ref(false)
const current = ref(null)

async function load() {
  loading.value = true
  try {
    const res = await getAdminFiles({ keyword: keyword.value, status: status.value, fileType: fileType.value, page: page.value, pageSize })
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
async function remove(row) {
  await ElMessageBox.confirm(`确认删除文件 ${row.fileName}？`, '删除确认', { type: 'warning' })
  await deleteAdminFile(row.id)
  ElMessage.success('文件已删除')
  load()
}
onMounted(load)
</script>

<style scoped>
.thumb {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  object-fit: cover;
}
.preview-img {
  width: 100%;
  max-height: 220px;
  margin-bottom: 16px;
  border-radius: 12px;
  object-fit: cover;
}
</style>
