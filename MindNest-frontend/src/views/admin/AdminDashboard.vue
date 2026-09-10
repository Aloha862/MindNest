<template>
  <main>
    <PageHeader title="后台首页" subtitle="系统运行情况一览" />
    <section class="admin-stats">
      <StatCard label="用户数量" :value="data.userCount" hint="实时统计" :icon="Users" />
      <StatCard label="上传文件" :value="data.fileCount" hint="今日 +2" color="#8b5cf6" :icon="FileImage" />
      <StatCard label="识别任务" :value="data.recognitionTaskCount" hint="今日 +1" color="#22c55e" :icon="Cpu" />
      <StatCard label="题目卡片" :value="data.questionCount" hint="近 7 日 +6" color="#f59e0b" :icon="BookOpen" />
      <StatCard label="今日上传" :value="data.todayUploadCount" hint="" compact :icon="BarChart3" />
      <StatCard label="今日识别" :value="data.todayRecognitionCount" hint="" compact color="#8b5cf6" :icon="BarChart3" />
      <StatCard label="模型调用" :value="data.modelCallCount" hint="" compact color="#22c55e" :icon="BarChart3" />
      <StatCard label="失败任务" :value="data.failedTaskCount" hint="" compact color="#ef4444" :icon="BarChart3" />
      <StatCard label="OCR空结果" :value="data.ocrEmptyCount" hint="" compact color="#f59e0b" :icon="BarChart3" />
      <StatCard label="VLM JSON错误" :value="data.vlmInvalidJsonCount" hint="" compact color="#ef4444" :icon="BarChart3" />
    </section>
    <section class="admin-grid">
      <article class="panel wide"><h2>每日上传趋势</h2><UploadTrendChart :data="data.uploadTrend" /></article>
      <article class="panel"><h2>任务状态分布</h2><SubjectPieChart :data="statusPie" /></article>
      <article class="panel"><h2>失败原因 Top</h2><div v-for="item in data.failureReasons" :key="item.name" class="list-row"><StatusTag status="failed" :label="item.name" /><em>{{ item.value }}</em></div><el-empty v-if="!data.failureReasons?.length" description="暂无失败数据" /></article>
      <article class="panel"><h2>模型耗时</h2><div v-for="item in data.modelLatency" :key="item.modelType" class="list-row"><span>{{ item.modelType }}</span><small>avg {{ item.avg }}ms / P95 {{ item.p95 }}ms</small></div><el-empty v-if="!data.modelLatency?.length" description="暂无耗时数据" /></article>
      <article class="panel"><h2>最近模型日志</h2><div v-for="log in data.recentLogs" :key="log.id" class="list-row"><StatusTag :status="log.status" :label="log.modelType" /><span>{{ log.modelName }}</span><em>{{ log.costTime }}</em></div></article>
      <article class="panel"><h2>最近上传文件</h2><div v-for="file in data.recentFiles" :key="file.id" class="file-row"><img :src="file.originalImageUrl" alt="" /><span>{{ file.fileName }}<small>{{ file.createdAt }}</small></span><StatusTag :status="file.status" /></div></article>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive } from 'vue'
import { BarChart3, BookOpen, Cpu, FileImage, Users } from 'lucide-vue-next'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/admin/StatCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import UploadTrendChart from '@/components/chart/UploadTrendChart.vue'
import SubjectPieChart from '@/components/chart/SubjectPieChart.vue'
import { getAdminDashboard } from '@/api/admin'

const data = reactive({ userCount: 0, fileCount: 0, recognitionTaskCount: 0, questionCount: 0, todayUploadCount: 0, todayRecognitionCount: 0, modelCallCount: 0, failedTaskCount: 0, ocrEmptyCount: 0, vlmInvalidJsonCount: 0, taskStatusDistribution: [], recentLogs: [], recentFiles: [], uploadTrend: [], failureReasons: [], modelLatency: [] })
const statusPie = computed(() => data.taskStatusDistribution)
onMounted(async () => Object.assign(data, (await getAdminDashboard()).data))
</script>

<style scoped>
.admin-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.admin-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 18px;
  margin-top: 22px;
}

.panel {
  padding: 22px;
}

.wide {
  min-height: 320px;
}

h2 {
  margin-top: 0;
}

.list-row,
.file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 0;
}

.list-row em {
  margin-left: auto;
  color: var(--sm-muted);
  font-style: normal;
}

.file-row img {
  width: 40px;
  height: 40px;
  border-radius: 9px;
  object-fit: cover;
}

.file-row span {
  flex: 1;
}

small {
  display: block;
  color: var(--sm-muted);
}

@media (max-width: 1000px) {
  .admin-stats,
  .admin-grid {
    grid-template-columns: 1fr;
  }
}
</style>
