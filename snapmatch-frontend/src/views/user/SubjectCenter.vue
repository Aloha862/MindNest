<template>
  <main class="page-shell subject-page">
    <PageHeader title="科目与知识点" subtitle="按科目和知识点聚合题目与错题，快速定位薄弱模块" />

    <section class="subject-grid">
      <StatCard
        v-for="(item, i) in subjects"
        :key="item.name"
        :label="item.name"
        :value="item.value"
        hint="题目卡片"
        :color="colors[i % colors.length]"
        :icon="Reading"
      />
    </section>

    <section class="content-grid">
      <section class="panel chart-panel">
        <div class="panel-title">
          <h2>科目题目数量</h2>
          <span>{{ totalQuestionCount }} 题</span>
        </div>
        <div class="chart-wrap">
          <TypeBarChart :data="subjects" />
        </div>
      </section>

      <section class="panel knowledge-panel">
        <div class="panel-title">
          <h2>知识点聚合</h2>
          <span>{{ filteredKnowledgeStats.length }} 个</span>
        </div>

        <div class="toolbar">
          <el-select v-model="filters.subject" clearable placeholder="按科目筛选">
            <el-option v-for="item in subjects" :key="item.name" :label="item.name" :value="item.name" />
          </el-select>
          <el-input v-model="filters.keyword" clearable placeholder="搜索知识点或科目" />
        </div>

        <el-table :data="pagedKnowledgeStats" height="332" style="width: 100%">
          <el-table-column prop="name" label="知识点" min-width="150" show-overflow-tooltip />
          <el-table-column label="科目" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ subjectText(row) }}</template>
          </el-table-column>
          <el-table-column prop="value" label="题目" width="76" />
          <el-table-column prop="wrongCount" label="错题" width="76" />
          <el-table-column prop="weakCount" label="薄弱" width="76" />
          <el-table-column label="操作" width="132" fixed="right">
            <template #default="{ row }">
              <el-button size="small" link type="primary" @click="goQuestions(row)">题目</el-button>
              <el-button size="small" link type="warning" @click="goWrong(row)">错题</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-if="filteredKnowledgeStats.length > pageSize"
          v-model:current-page="currentPage"
          background
          small
          layout="prev, pager, next"
          :page-size="pageSize"
          :total="filteredKnowledgeStats.length"
          class="knowledge-pager"
        />
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Reading } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import TypeBarChart from '@/components/chart/TypeBarChart.vue'
import { getQuestionKnowledgeStats, getQuestionStatistics } from '@/api/question'

const router = useRouter()
const subjects = ref([])
const knowledgeStats = ref([])
const currentPage = ref(1)
const pageSize = 8
const filters = reactive({ subject: '', keyword: '' })
const colors = ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444', '#4fb5d3']

const totalQuestionCount = computed(() => subjects.value.reduce((sum, item) => sum + Number(item.value || 0), 0))

const filteredKnowledgeStats = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()
  return knowledgeStats.value.filter((item) => {
    const subjectsOfPoint = item.subjects || (item.subject ? [item.subject] : [])
    const matchSubject = !filters.subject || subjectsOfPoint.includes(filters.subject)
    const text = `${item.name || ''} ${subjectsOfPoint.join(' ')}`.toLowerCase()
    const matchKeyword = !keyword || text.includes(keyword)
    return matchSubject && matchKeyword
  })
})

const pagedKnowledgeStats = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredKnowledgeStats.value.slice(start, start + pageSize)
})

function subjectText(row) {
  return (row.subjects || (row.subject ? [row.subject] : [])).join(' / ') || '-'
}

function goQuestions(row) {
  router.push(`/user/questions?knowledgePoint=${encodeURIComponent(row.name)}`)
}

function goWrong(row) {
  router.push(`/user/wrong-questions?knowledgePoint=${encodeURIComponent(row.name)}`)
}

watch(filters, () => {
  currentPage.value = 1
})

onMounted(async () => {
  subjects.value = (await getQuestionStatistics()).data.subjectStats || []
  knowledgeStats.value = (await getQuestionKnowledgeStats()).data || []
})
</script>

<style scoped>
.subject-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.subject-grid :deep(.stat-card) {
  height: 118px;
  min-height: 118px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 18px;
  margin-top: 24px;
}

.chart-panel,
.knowledge-panel {
  height: 520px;
  padding: 22px;
  overflow: hidden;
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-title h2 {
  margin: 0;
  font-size: 20px;
}

.panel-title span {
  flex: none;
  padding: 5px 10px;
  border-radius: 999px;
  color: #2563eb;
  background: #eff6ff;
  font-size: 12px;
  font-weight: 700;
}

.chart-wrap {
  height: 438px;
  min-height: 438px;
}

.toolbar {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 10px;
  margin-bottom: 14px;
}

.knowledge-pager {
  justify-content: center;
  margin-top: 14px;
}

@media (max-width: 900px) {
  .subject-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .chart-panel,
  .knowledge-panel {
    height: auto;
    min-height: 520px;
  }

  .toolbar {
    grid-template-columns: 1fr;
  }
}
</style>
