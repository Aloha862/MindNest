<template>
  <main class="page-shell reports-page">
    <section class="page-title">
      <div>
        <p>学习报告</p>
        <h1>今日学习闭环</h1>
        <span>{{ daily.content || '暂无报告数据，开始一次专注学习后会自动生成统计。' }}</span>
      </div>
      <el-button type="primary" @click="refresh"><RefreshCw />刷新报告</el-button>
    </section>

    <section class="stats-grid">
      <StatCard label="总学习时长" :value="formatDuration(stats.totalDuration)" hint="今日累计" :icon="Clock" />
      <StatCard label="有效专注" :value="formatDuration(stats.effectiveDuration)" :hint="`${stats.focusEfficiency || 0}% 效率`" color="#22c55e" :icon="BadgeCheck" />
      <StatCard label="题目数量" :value="stats.questionCount || 0" hint="今日沉淀" color="#8b5cf6" :icon="BookOpen" />
      <StatCard label="错题数量" :value="stats.wrongCount || 0" hint="今日新增" color="#ef4444" :icon="AlertCircle" />
    </section>

    <section class="report-grid">
      <article class="panel report-card">
        <header>
          <h2>复习建议</h2>
          <span>{{ daily.date }}</span>
        </header>
        <ol v-if="daily.recommendations?.length">
          <li v-for="item in daily.recommendations" :key="item">{{ item }}</li>
        </ol>
        <EmptyState v-else title="暂无建议" description="完成题目识别和专注学习后会生成个性化建议。" />
      </article>

      <article class="panel insight-card">
        <h2>薄弱知识点</h2>
        <div v-if="daily.weakKnowledgePoints?.length" class="bar-list">
          <div v-for="item in daily.weakKnowledgePoints" :key="item.name">
            <span>{{ item.name }}</span>
            <strong>{{ item.value }}</strong>
            <i :style="{ width: `${Math.min(100, item.value * 24)}%` }" />
          </div>
        </div>
        <EmptyState v-else title="暂无知识点数据" description="识别题目后会按知识点聚合。" />
      </article>

      <article class="panel insight-card">
        <h2>错因分布</h2>
        <div v-if="daily.errorCauseStats?.length" class="cause-list">
          <p v-for="item in daily.errorCauseStats" :key="item.name">
            <span>{{ item.name }}</span>
            <em>{{ item.value }} 次</em>
          </p>
        </div>
        <EmptyState v-else title="暂无错因数据" description="错题分析完成后会沉淀错因标签。" />
      </article>
    </section>

    <section class="panel sessions-panel">
      <header>
        <h2>学习 session</h2>
        <span>最近 {{ sessions.length }} 条</span>
      </header>
      <el-table :data="sessions" v-loading="loading" empty-text="暂无学习 session">
        <el-table-column label="标题" min-width="160">
          <template #default="{ row }">
            <strong>{{ row.title }}</strong>
            <small>{{ row.startTime }}</small>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status === 'active' ? '进行中' : '已结束' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="有效专注" width="150">
          <template #default="{ row }">{{ formatDuration(row.effectiveDuration) }}</template>
        </el-table-column>
        <el-table-column label="专注分" prop="averageFocusScore" width="100" />
        <el-table-column label="手机分心" width="110">
          <template #default="{ row }">{{ row.distractionCount }} 次</template>
        </el-table-column>
        <el-table-column label="摘要" min-width="260" prop="summary" show-overflow-tooltip />
      </el-table>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { AlertCircle, BadgeCheck, BookOpen, Clock, RefreshCw } from 'lucide-vue-next'
import { getDailyReport, getStudySessions } from '@/api/report'
import StatCard from '@/components/admin/StatCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const daily = reactive({ date: '', content: '', stats: {}, recommendations: [], weakKnowledgePoints: [], errorCauseStats: [] })
const sessions = ref([])
const loading = ref(false)
const stats = computed(() => daily.stats || {})

function formatDuration(seconds = 0) {
  const safe = Math.max(0, Number(seconds) || 0)
  const h = Math.floor(safe / 3600)
  const m = Math.floor((safe % 3600) / 60)
  const s = safe % 60
  if (h) return `${h}时${m}分`
  if (m) return `${m}分${s}秒`
  return `${s}秒`
}

async function refresh() {
  loading.value = true
  try {
    const [dailyRes, sessionsRes] = await Promise.all([
      getDailyReport(),
      getStudySessions({ page: 1, pageSize: 10 })
    ])
    Object.assign(daily, dailyRes.data)
    sessions.value = sessionsRes.data?.list || []
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>

<style scoped>
.reports-page {
  padding: 28px 0 80px;
}

.page-title,
.stats-grid,
.report-grid {
  display: grid;
  gap: 18px;
}

.page-title {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  margin-bottom: 18px;
}

.page-title p,
.page-title h1,
.page-title span,
h2 {
  margin: 0;
}

.page-title p {
  color: var(--sm-primary);
  font-weight: 800;
}

.page-title h1 {
  margin: 6px 0;
  font-size: 30px;
}

.page-title span {
  display: block;
  max-width: 820px;
  color: var(--sm-muted);
  line-height: 1.7;
}

.stats-grid {
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 18px;
}

.report-grid {
  grid-template-columns: 1.2fr 0.9fr 0.9fr;
  margin-bottom: 18px;
}

.report-card,
.insight-card,
.sessions-panel {
  padding: 20px;
}

.report-card header,
.sessions-panel header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.report-card header span,
.sessions-panel header span,
small {
  color: var(--sm-muted);
}

ol {
  display: grid;
  gap: 12px;
  margin: 0;
  padding-left: 22px;
  line-height: 1.7;
}

.bar-list {
  display: grid;
  gap: 14px;
}

.bar-list div {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px;
  gap: 12px;
  padding-bottom: 10px;
  overflow: hidden;
}

.bar-list i {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 4px;
  border-radius: 999px;
  background: var(--sm-primary);
}

.bar-list span,
.cause-list span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cause-list {
  display: grid;
  gap: 12px;
}

.cause-list p {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin: 0;
  padding: 10px 0;
  border-bottom: 1px solid var(--sm-border);
}

.cause-list em {
  color: var(--sm-muted);
  font-style: normal;
  white-space: nowrap;
}

.sessions-panel strong,
.sessions-panel small {
  display: block;
}

@media (max-width: 980px) {
  .page-title,
  .stats-grid,
  .report-grid {
    grid-template-columns: 1fr;
  }
}
</style>
