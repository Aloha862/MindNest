<template>
  <main class="page-shell question-page">
    <PageHeader title="题目卡片" :subtitle="`共 ${total} 张题目卡片`">
      <el-button @click="goExport"><Download />导出</el-button>
    </PageHeader>
    <QuestionFilter :query="query" :subjects="subjects" @reset="reset" />
    <section v-loading="loading" class="question-grid">
      <QuestionCard v-for="question in rows" :key="question.id" :question="question" @delete="remove" />
    </section>
    <el-empty v-if="!loading && !rows.length" description="暂无题目卡片" />
    <el-pagination
      v-if="total > query.pageSize"
      v-model:current-page="query.page"
      background
      layout="prev, pager, next, jumper"
      :total="total"
      :page-size="query.pageSize"
      class="pager"
    />
  </main>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import QuestionFilter from '@/components/question/QuestionFilter.vue'
import QuestionCard from '@/components/question/QuestionCard.vue'
import { deleteQuestion, getQuestions, getSubjects } from '@/api/question'

const router = useRouter()
const query = reactive({ keyword: '', subject: '', questionType: '', difficulty: '', page: 1, pageSize: 6 })
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const subjects = ref(['数学', '英语', '计算机', '政治', '专业课', '物理'])

async function load() {
  loading.value = true
  try {
    const res = await getQuestions(query)
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

function reset() {
  Object.assign(query, { keyword: '', subject: '', questionType: '', difficulty: '', page: 1 })
}

function goExport() {
  router.push({ path: '/user/export', query: { ...query } })
}

async function remove(question) {
  await ElMessageBox.confirm(`确认删除题目 ${question.title}？`, '删除确认', { type: 'warning' })
  await deleteQuestion(question.id)
  ElMessage.success('题目已删除')
  load()
}

watch(query, () => {
  load()
})
onMounted(() => {
  loadSubjects()
  load()
})
</script>

<style scoped>
.question-grid {
  display: grid;
  min-height: 220px;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 20px;
}

.pager {
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 980px) {
  .question-grid {
    grid-template-columns: 1fr;
  }
}
</style>
