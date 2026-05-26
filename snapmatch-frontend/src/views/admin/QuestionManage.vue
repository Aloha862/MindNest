<template>
  <main>
    <PageHeader title="题目管理" :subtitle="`共 ${total} 道题目`" />
    <AdminTable :rows="rows" :loading="loading" :total="total" :page="page" :page-size="pageSize" placeholder="搜索题目标题" @search="onSearch" @page-change="onPageChange">
      <template #filters>
        <el-select v-model="subject" placeholder="全部科目" clearable @change="refresh"><el-option v-for="item in subjects" :key="item" :label="item" :value="item" /></el-select>
        <el-select v-model="questionType" placeholder="全部题型" clearable @change="refresh"><el-option v-for="item in types" :key="item" :label="item" :value="item" /></el-select>
        <el-select v-model="difficulty" placeholder="全部难度" clearable @change="refresh"><el-option label="基础" value="基础" /><el-option label="进阶" value="进阶" /><el-option label="挑战" value="挑战" /></el-select>
      </template>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="title" label="题目标题" min-width="260" />
      <el-table-column prop="subject" label="科目" />
      <el-table-column prop="questionType" label="题型" />
      <el-table-column label="难度"><template #default="{ row }"><el-tag :type="difficultyType(row.difficulty)">{{ row.difficulty }}</el-tag></template></el-table-column>
      <el-table-column label="知识点" min-width="180"><template #default="{ row }">{{ (row.knowledgePoints || []).join(' / ') }}</template></el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="190" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <div class="table-actions">
            <button class="icon-button" @click="$router.push(`/admin/questions/${row.id}`)"><View /></button>
            <button class="icon-button" @click="$router.push(`/admin/questions/${row.id}`)"><EditPen /></button>
            <button class="icon-button danger" @click="remove(row)"><Delete /></button>
          </div>
        </template>
      </el-table-column>
    </AdminTable>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, EditPen, View } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import AdminTable from '@/components/admin/AdminTable.vue'
import { getAdminQuestions } from '@/api/admin'
import { deleteQuestion, getSubjects } from '@/api/question'
import { difficultyType } from '@/utils/format'

const rows = ref([])
const keyword = ref('')
const subject = ref('')
const questionType = ref('')
const difficulty = ref('')
const subjects = ref(['数学', '英语', '计算机', '政治', '专业课', '物理'])
const types = ['选择题', '填空题', '简答题', '计算题', '阅读理解']
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await getAdminQuestions({ keyword: keyword.value, subject: subject.value, questionType: questionType.value, difficulty: difficulty.value, page: page.value, pageSize })
    rows.value = res.data.list || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}
async function loadSubjects() {
  const res = await getSubjects()
  subjects.value = (res.data || []).map((item) => item.name || item).filter(Boolean)
}
function refresh() { page.value = 1; load() }
function onSearch(value) { keyword.value = value; refresh() }
function onPageChange(value) { page.value = value; load() }
async function remove(row) {
  await ElMessageBox.confirm(`确认删除题目 ${row.title}？`, '删除确认', { type: 'warning' })
  await deleteQuestion(row.id)
  ElMessage.success('题目已删除')
  load()
}
onMounted(() => {
  loadSubjects()
  load()
})
</script>
