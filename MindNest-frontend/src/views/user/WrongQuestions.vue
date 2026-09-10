<template>
  <main class="page-shell wrong-page">
    <PageHeader title="错题本" :subtitle="`共 ${total} 条错题记录`">
      <el-button type="primary" :disabled="!rows.length" @click="startReview">开始复习</el-button>
    </PageHeader>

    <AdminTable
      :rows="rows"
      :loading="loading"
      :total="total"
      :page="query.page"
      :page-size="query.pageSize"
      placeholder="搜索题目、知识点或备注"
      @search="onSearch"
      @page-change="onPageChange"
    >
      <template #filters>
        <el-select v-model="query.subject" placeholder="全部科目" clearable @change="refresh">
          <el-option v-for="item in subjects" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="query.masteryStatus" placeholder="全部状态" clearable @change="refresh">
          <el-option label="未复习" value="unreviewed" />
          <el-option label="复习中" value="reviewing" />
          <el-option label="需强化" value="weak" />
          <el-option label="已掌握" value="mastered" />
        </el-select>
      </template>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="题目标题" min-width="240">
        <template #default="{ row }">{{ row.question?.title || '未命名题目' }}</template>
      </el-table-column>
      <el-table-column label="科目" width="110">
        <template #default="{ row }">{{ row.question?.subject || '未知' }}</template>
      </el-table-column>
      <el-table-column label="知识点" min-width="170">
        <template #default="{ row }">{{ knowledgeText(row) }}</template>
      </el-table-column>
      <el-table-column label="复习次数" width="100">
        <template #default="{ row }">{{ row.reviewCount || 0 }}</template>
      </el-table-column>
      <el-table-column label="最近结果" width="110">
        <template #default="{ row }">{{ row.latestAttempt?.result || '暂无' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }"><StatusTag :status="row.masteryStatus" :label="masteryLabel(row.masteryStatus)" /></template>
      </el-table-column>
      <el-table-column label="操作" width="190">
        <template #default="{ row }">
          <div class="table-actions">
            <el-button size="small" link type="primary" @click="openReview(row)">复习</el-button>
            <el-button size="small" link @click="openQuestion(row)">详情</el-button>
            <el-button size="small" link type="success" @click="markMastered(row)">掌握</el-button>
          </div>
        </template>
      </el-table-column>
    </AdminTable>

    <el-drawer v-model="reviewVisible" title="错题重做" size="560px">
      <template v-if="activeRecord">
        <section class="review-block">
          <div class="badges">
            <el-tag>{{ activeRecord.question?.subject }}</el-tag>
            <el-tag type="info">{{ activeRecord.question?.questionType }}</el-tag>
          </div>
          <h3>{{ activeRecord.question?.title }}</h3>
          <MathText :text="activeRecord.question?.content" />
          <div v-if="activeRecord.question?.options?.length" class="options">
            <p v-for="(option, index) in activeRecord.question.options" :key="index">{{ optionText(option, index) }}</p>
          </div>
        </section>

        <section v-if="!showSolution" class="review-actions">
          <el-input v-model="attempt.note" type="textarea" :rows="3" placeholder="可记录本次思路或卡住的位置" />
          <el-radio-group v-model="attempt.selfRating">
            <el-radio-button label="easy">轻松</el-radio-button>
            <el-radio-button label="normal">一般</el-radio-button>
            <el-radio-button label="hard">困难</el-radio-button>
          </el-radio-group>
          <div>
            <el-button type="success" @click="submitAttempt('correct')">答对</el-button>
            <el-button type="danger" @click="submitAttempt('wrong')">答错</el-button>
            <el-button type="warning" @click="submitAttempt('unsure')">不确定</el-button>
          </div>
        </section>

        <section v-else class="solution">
          <h3>VLM 解析</h3>
          <p><strong>答案：</strong>{{ vlm.answer || activeRecord.question?.answer || '暂无' }}</p>
          <p><strong>摘要：</strong>{{ vlm.analysisSummary || activeRecord.question?.analysisSummary || '暂无' }}</p>
          <div v-if="vlm.detailedAnalysis || activeRecord.question?.detailedAnalysis">
            <strong>详细解析</strong>
            <MathText :text="vlm.detailedAnalysis || activeRecord.question?.detailedAnalysis" />
          </div>
          <ol v-if="solutionSteps.length">
            <li v-for="item in solutionSteps" :key="item">{{ item }}</li>
          </ol>
          <el-button type="primary" @click="nextReview">下一题</el-button>
        </section>
      </template>
    </el-drawer>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import AdminTable from '@/components/admin/AdminTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import MathText from '@/components/common/MathText.vue'
import { getSubjects } from '@/api/question'
import { createWrongAttempt, getWrongRecords, masterWrongRecord } from '@/api/wrongRecord'

const router = useRouter()
const route = useRoute()
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const subjects = ref(['数学', '英语', '计算机', '政治', '专业课', '物理'])
const query = reactive({ keyword: '', subject: '', knowledgePoint: route.query.knowledgePoint || '', masteryStatus: '', page: 1, pageSize: 10 })
const reviewVisible = ref(false)
const activeRecord = ref(null)
const showSolution = ref(false)
const attempt = reactive({ selfRating: 'normal', note: '' })

const vlm = computed(() => activeRecord.value?.question?.vlmDetail || {})
const solutionSteps = computed(() => vlm.value.solutionSteps || activeRecord.value?.question?.solutionSteps || [])

function knowledgeText(row) {
  const points = row.question?.knowledgePoints || []
  return Array.isArray(points) && points.length ? points.join(' / ') : '无'
}

function masteryLabel(status) {
  return ({ unreviewed: '未复习', reviewing: '复习中', mastered: '已掌握', weak: '需强化' })[status] || status || '未复习'
}

function optionText(option, index) {
  if (typeof option === 'string') return option
  return `${option?.label || String.fromCharCode(65 + index)}. ${option?.text || option?.content || ''}`.trim()
}

async function load() {
  loading.value = true
  try {
    const res = await getWrongRecords(query)
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

function refresh() {
  query.page = 1
  load()
}

function onSearch(value) {
  query.keyword = value
  refresh()
}

function onPageChange(value) {
  query.page = value
  load()
}

function openQuestion(row) {
  const id = row.questionId || row.question?.id
  if (id) router.push(`/user/questions/${id}`)
}

function openReview(row) {
  activeRecord.value = row
  showSolution.value = false
  attempt.selfRating = 'normal'
  attempt.note = ''
  reviewVisible.value = true
}

function startReview() {
  const row = rows.value.find((item) => item.masteryStatus !== 'mastered') || rows.value[0]
  if (row) openReview(row)
}

async function submitAttempt(result) {
  const res = await createWrongAttempt(activeRecord.value.id, { result, selfRating: attempt.selfRating, note: attempt.note })
  activeRecord.value = res.data.record
  showSolution.value = true
  ElMessage.success('本次复习已记录')
  load()
}

async function markMastered(row) {
  await masterWrongRecord(row.id)
  ElMessage.success('错题已标记为掌握')
  load()
}

function nextReview() {
  const next = rows.value.find((item) => item.id !== activeRecord.value?.id && item.masteryStatus !== 'mastered')
  if (next) openReview(next)
  else reviewVisible.value = false
}

onMounted(() => {
  loadSubjects()
  load()
})
</script>

<style scoped>
.review-block,
.review-actions,
.solution {
  display: grid;
  gap: 14px;
}

.badges {
  display: flex;
  gap: 8px;
}

.options p {
  margin: 8px 0;
  padding: 10px;
  border: 1px solid var(--sm-border);
  border-radius: 8px;
}

.review-actions {
  margin-top: 18px;
}

.solution {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid var(--sm-border);
}
</style>
