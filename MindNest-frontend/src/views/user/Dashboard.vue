<template>
  <main class="page-shell user-dashboard">
    <section class="workspace-head">
      <div class="head-copy">
        <p>智学空间(MindNest)</p>
        <h1>你好，{{ auth.userInfo?.nickname || auth.userInfo?.username || '同学' }}</h1>
        <span>这里汇总题目识别、错因诊断、专注监督和复习建议。</span>
      </div>
      <div class="head-actions">
        <el-button type="primary" @click="$router.push('/user/upload')"><Upload />上传题目</el-button>
        <el-button @click="$router.push('/user/focus')"><Activity />开始专注</el-button>
      </div>
    </section>

    <section class="stats-grid">
      <StatCard label="今日有效专注" :value="formatDuration(data.todayFocus.effectiveDuration)" :hint="`${data.todayFocus.focusEfficiency}% 效率`" color="#22c55e" :icon="BadgeCheck" />
      <StatCard label="今日学习时长" :value="formatDuration(data.todayFocus.totalDuration)" :hint="`${data.todayFocus.sessionCount} 个 session`" :icon="Clock" />
      <StatCard label="今日题目" :value="data.todayQuestionCount" hint="识别与手动整理" color="#8b5cf6" :icon="BookOpen" />
      <StatCard label="今日错题" :value="data.todayWrongCount" hint="自动沉淀复习" color="#ef4444" :icon="AlertCircle" />
    </section>

    <section class="dashboard-grid">
      <article class="panel focus-panel">
        <header class="panel-head">
          <h2>学习状态</h2>
          <el-tag :type="data.todayFocus.currentState === 'active' ? 'success' : 'info'">{{ data.todayFocus.currentStateText }}</el-tag>
        </header>
        <div class="focus-content">
          <div class="focus-meter">
            <strong>{{ data.todayFocus.focusEfficiency || 0 }}%</strong>
            <span>今日专注效率</span>
          </div>
          <div class="focus-meta">
            <p>有效专注 {{ formatDuration(data.todayFocus.effectiveDuration) }}</p>
            <p>总学习 {{ formatDuration(data.todayFocus.totalDuration) }}</p>
            <el-button plain @click="$router.push('/user/reports')">查看学习报告</el-button>
          </div>
        </div>
      </article>

      <article class="panel review-panel">
        <header class="panel-head">
          <div>
            <h2>推荐复习</h2>
            <p>根据错题和知识点频次生成下一步复习方向</p>
          </div>
          <RouterLink to="/user/wrong-questions">错题本</RouterLink>
        </header>
        <div v-if="data.recommendedKnowledgePoints.length" class="review-list">
          <p v-for="item in data.recommendedKnowledgePoints" :key="item.name">
            <span>{{ item.name }}</span>
            <em>{{ item.value }} 道相关题</em>
          </p>
        </div>
        <EmptyState v-else title="暂无复习建议" description="完成题目识别后会根据知识点自动生成。" />
      </article>

      <article class="panel recent">
        <header class="panel-head">
          <h2>最近识别任务</h2>
          <RouterLink to="/user/history">查看全部</RouterLink>
        </header>
        <div v-if="data.recentTasks.length" class="task-list">
          <div v-for="task in data.recentTasks" :key="task.id" class="task-row">
            <span class="task-icon"><Camera /></span>
            <div class="task-main">
              <strong>{{ task.fileName }}</strong>
              <small>{{ task.createdAt }}</small>
            </div>
            <em>{{ task.progress }}%</em>
            <StatusTag :status="task.status" />
          </div>
        </div>
        <EmptyState v-else title="暂无识别任务" description="上传题目图片后会出现在这里。" />
      </article>

      <article class="panel chart-card subject-card">
        <header class="panel-head">
          <h2>科目分布</h2>
          <span>{{ data.subjectStats.length }} 类</span>
        </header>
        <SubjectPieChart :data="data.subjectStats" />
      </article>

      <article class="panel chart-card type-card">
        <header class="panel-head">
          <h2>题型分布</h2>
          <span>{{ data.typeStats.length }} 类</span>
        </header>
        <TypeBarChart :data="data.typeStats" />
      </article>

      <article class="panel question-panel">
        <header class="panel-head">
          <div>
            <h2>最近生成题目卡片</h2>
            <p>从图片、OCR 和 VLM 分析沉淀出的结构化学习资料</p>
          </div>
          <RouterLink to="/user/questions">查看全部</RouterLink>
        </header>
        <div v-if="data.recentQuestions.length" class="question-grid">
          <QuestionCard v-for="question in data.recentQuestions.slice(0, 2)" :key="question.id" :question="question" :deletable="false" />
        </div>
        <EmptyState v-else title="暂无题目卡片" description="上传并识别题目后会生成卡片。" />
      </article>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { Activity, AlertCircle, BadgeCheck, BookOpen, Camera, Clock, Upload } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'
import { getDashboard } from '@/api/user'
import StatCard from '@/components/admin/StatCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SubjectPieChart from '@/components/chart/SubjectPieChart.vue'
import TypeBarChart from '@/components/chart/TypeBarChart.vue'
import QuestionCard from '@/components/question/QuestionCard.vue'

const auth = useAuthStore()
const data = reactive({
  uploadCount: 0,
  recognitionCount: 0,
  questionCount: 0,
  subjectCount: 0,
  todayQuestionCount: 0,
  todayWrongCount: 0,
  todayFocus: { totalDuration: 0, effectiveDuration: 0, focusEfficiency: 0, sessionCount: 0, currentState: 'idle', currentStateText: '未开始' },
  recommendedKnowledgePoints: [],
  recentTasks: [],
  recentQuestions: [],
  subjectStats: [],
  typeStats: []
})

function formatDuration(seconds = 0) {
  const safe = Math.max(0, Number(seconds) || 0)
  const h = Math.floor(safe / 3600)
  const m = Math.floor((safe % 3600) / 60)
  if (h) return `${h}时${m}分`
  if (m) return `${m}分钟`
  return `${safe}秒`
}

onMounted(async () => Object.assign(data, (await getDashboard()).data))
</script>

<style scoped>
.user-dashboard {
  padding: 30px 0 80px;
}

.workspace-head,
.stats-grid,
.dashboard-grid,
.question-grid {
  display: grid;
  gap: 18px;
}

.workspace-head {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  margin-bottom: 18px;
}

.head-copy p,
.head-copy h1,
.head-copy span,
.panel-head h2,
.panel-head p {
  margin: 0;
}

.head-copy p {
  color: var(--sm-primary);
  font-weight: 800;
}

.head-copy h1 {
  margin: 7px 0;
  font-size: 30px;
  line-height: 1.2;
}

.head-copy span,
.panel-head p,
small {
  color: var(--sm-muted);
}

.head-actions {
  display: flex;
  gap: 10px;
}

.head-actions svg {
  width: 16px;
}

.stats-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.dashboard-grid {
  grid-template-columns: repeat(12, minmax(0, 1fr));
  align-items: stretch;
  margin-top: 18px;
}

.panel {
  min-width: 0;
  padding: 20px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.panel-head h2 {
  font-size: 22px;
  line-height: 1.25;
}

.panel-head p {
  margin-top: 6px;
  line-height: 1.55;
}

.panel-head a,
.review-panel a {
  flex: none;
  color: var(--sm-primary);
  font-weight: 600;
}

.panel-head > span {
  flex: none;
  color: var(--sm-muted);
}

.focus-panel {
  grid-column: span 5;
}

.review-panel {
  grid-column: span 7;
}

.recent,
.type-card {
  grid-column: span 5;
}

.subject-card,
.question-panel {
  grid-column: span 7;
}

.focus-content {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  align-items: center;
  gap: 22px;
  min-height: 196px;
}

.focus-meter {
  display: grid;
  place-items: center;
  align-content: center;
  width: 164px;
  height: 164px;
  border-radius: 50%;
  background: radial-gradient(circle at center, #ffffff 0 38%, #eef2ff 39% 100%);
}

.focus-meter strong {
  color: var(--sm-primary);
  font-size: 38px;
  line-height: 1;
}

.focus-meter span,
.focus-meta p {
  color: var(--sm-muted);
}

.focus-meta {
  display: grid;
  gap: 10px;
  align-content: center;
}

.focus-meta p {
  margin: 0;
}

.focus-meta .el-button {
  width: max-content;
}

.review-panel {
  min-height: 260px;
}

.review-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.review-list p {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
  margin: 0;
  padding: 14px;
  border: 1px solid var(--sm-border);
  border-radius: 12px;
  background: #f8fafc;
}

.review-list span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 700;
}

.review-list em {
  flex: none;
  color: var(--sm-muted);
  font-style: normal;
  white-space: nowrap;
}

.task-list {
  display: grid;
  gap: 2px;
}

.task-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) 58px minmax(74px, max-content);
  gap: 12px;
  align-items: center;
  min-height: 54px;
  padding: 8px 0;
}

.task-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  color: var(--sm-primary);
  background: #eef4ff;
}

.task-icon svg {
  width: 18px;
}

.task-main {
  min-width: 0;
}

.task-main strong,
.task-main small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row em {
  color: var(--sm-muted);
  font-style: normal;
  text-align: right;
}

.task-row :deep(.status-tag) {
  justify-self: end;
}

.chart-card :deep(.chart) {
  height: 286px;
}

.question-panel {
  overflow: hidden;
}

.question-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.question-grid :deep(.question-card) {
  height: 240px;
  min-height: 240px;
  max-height: 240px;
  box-shadow: none;
}

.question-panel :deep(.empty),
.review-panel :deep(.empty),
.recent :deep(.empty) {
  min-height: 168px;
}

@media (max-width: 980px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .focus-panel,
  .review-panel,
  .recent,
  .type-card,
  .subject-card,
  .question-panel {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .workspace-head,
  .stats-grid,
  .question-grid,
  .review-list {
    grid-template-columns: 1fr;
  }

  .workspace-head {
    align-items: start;
  }

  .head-actions {
    flex-wrap: wrap;
  }

  .focus-content {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }

  .focus-meta .el-button {
    justify-self: center;
  }
}
</style>
