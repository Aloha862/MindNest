<template>
  <main class="page-shell user-dashboard">
    <section class="welcome sm-gradient">
      <div>
        <p>你好，{{ auth.userInfo?.nickname || auth.userInfo?.username || '用户' }}</p>
        <h1>今天想整理哪些学习资料？</h1>
        <span>上传作业、试卷或错题图片，SnapMatch 会自动帮你生成题目卡片并分类。</span>
      </div>
      <el-button size="large" @click="$router.push('/user/upload')"><Upload />立即上传</el-button>
    </section>

    <section class="stats-grid">
      <StatCard label="上传文件数" :value="data.uploadCount" hint="本月 +3" :icon="Upload" />
      <StatCard label="识别任务数" :value="data.recognitionCount" hint="实时同步" color="#8b5cf6" :icon="ScanLine" />
      <StatCard label="题目卡片数" :value="data.questionCount" hint="后端统计" color="#22c55e" :icon="BookOpen" />
      <StatCard label="涉及科目数" :value="data.subjectCount" hint="覆盖主要学科" color="#f59e0b" :icon="FolderTree" />
    </section>

    <section class="dashboard-grid">
      <article class="panel recent">
        <header><h2>最近识别任务</h2><RouterLink to="/user/history">查看全部 →</RouterLink></header>
        <div v-for="task in data.recentTasks" :key="task.id" class="task-row">
          <span><Camera /></span>
          <div><strong>{{ task.fileName }}</strong><small>{{ task.createdAt }}</small></div>
          <em>{{ task.progress }}%</em>
          <StatusTag :status="task.status" />
        </div>
      </article>
      <article class="panel chart-card">
        <h2>科目分布</h2>
        <SubjectPieChart :data="data.subjectStats" />
      </article>
      <article class="panel chart-wide">
        <h2>题型分布</h2>
        <TypeBarChart :data="data.typeStats" />
      </article>
      <article class="panel usage">
        <h2>使用流程</h2>
        <p><Camera />上传图片<span>支持拖拽 / 点击上传</span></p>
        <p><Sparkles />智能识别<span>OCR + VLM 自动分析</span></p>
        <p><Layers />整理复习<span>按科目/题型分类管理</span></p>
      </article>
    </section>

    <PageHeader title="最近生成题目卡片" subtitle="点击查看详情，或在题目卡片页面继续整理" />
    <div class="question-grid">
      <QuestionCard v-for="question in data.recentQuestions" :key="question.id" :question="question" />
    </div>
  </main>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { BookOpen, Camera, FolderTree, Layers, ScanLine, Sparkles, Upload } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'
import { getDashboard } from '@/api/user'
import StatCard from '@/components/admin/StatCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SubjectPieChart from '@/components/chart/SubjectPieChart.vue'
import TypeBarChart from '@/components/chart/TypeBarChart.vue'
import QuestionCard from '@/components/question/QuestionCard.vue'

const auth = useAuthStore()
const data = reactive({ uploadCount: 0, recognitionCount: 0, questionCount: 0, subjectCount: 0, recentTasks: [], recentQuestions: [], subjectStats: [], typeStats: [] })

onMounted(async () => Object.assign(data, (await getDashboard()).data))
</script>

<style scoped>
.user-dashboard {
  padding-bottom: 80px;
}

.welcome {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 28px 0 20px;
  padding: 28px;
  border-radius: 18px;
  color: #fff;
}

.welcome p,
.welcome h1,
.welcome span {
  margin: 0;
}

.welcome h1 {
  margin: 8px 0;
  font-size: 24px;
}

.welcome span {
  opacity: 0.86;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 18px;
  margin-top: 18px;
}

.panel {
  padding: 22px;
}

.recent header {
  display: flex;
  justify-content: space-between;
}

h2 {
  margin: 0 0 18px;
  font-size: 18px;
}

.recent a {
  color: var(--sm-primary);
}

.task-row {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) 64px minmax(76px, max-content);
  gap: 14px;
  align-items: center;
  padding: 12px 0;
}

.task-row :deep(.status-tag) {
  justify-self: end;
}

.task-row > div {
  min-width: 0;
}

.task-row strong,
.task-row small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row > span,
.usage p > svg {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  color: var(--sm-primary);
  background: #eef4ff;
}

strong,
small {
  display: block;
}

small {
  color: var(--sm-muted);
}

em {
  color: var(--sm-muted);
  font-style: normal;
}

.chart-wide {
  grid-column: span 1;
}

.usage p {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 16px 0;
  font-weight: 700;
}

.usage span {
  display: block;
  color: var(--sm-muted);
  font-weight: 400;
}

.question-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 980px) {
  .stats-grid,
  .dashboard-grid,
  .question-grid {
    grid-template-columns: 1fr;
  }

  .welcome {
    align-items: flex-start;
    flex-direction: column;
    gap: 18px;
  }
}
</style>
