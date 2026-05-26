<template>
  <main class="page-shell export-page">
    <PageHeader title="导出中心" subtitle="导出题目、错题本、整批联卷或指定知识点，内容包含 OCR 与 VLM 完整解析" />
    <section class="export-grid">
      <div>
        <section class="panel block">
          <h3>导出范围</h3>
          <div class="choice-grid">
            <button v-for="item in ranges" :key="item.value" :class="{ active: form.range === item.value }" @click="form.range = item.value">
              {{ item.label }}
            </button>
          </div>
        </section>

        <section class="panel block">
          <h3>筛选条件</h3>
          <div class="filter-grid">
            <el-select v-model="form.subject" clearable placeholder="科目">
              <el-option v-for="item in subjects" :key="item" :label="item" :value="item" />
            </el-select>
            <el-input v-if="form.range === 'task'" v-model.number="form.taskId" placeholder="识别任务 ID" />
            <el-input v-if="form.range === 'batch'" v-model="form.batchId" placeholder="批次 batchId" />
            <el-input v-if="form.range === 'knowledge'" v-model="form.knowledgePoint" placeholder="知识点" />
            <el-select v-if="['wrong', 'mastery'].includes(form.range)" v-model="form.masteryStatus" clearable placeholder="掌握状态">
              <el-option label="未复习" value="unreviewed" />
              <el-option label="复习中" value="reviewing" />
              <el-option label="需强化" value="weak" />
              <el-option label="已掌握" value="mastered" />
            </el-select>
            <el-date-picker v-if="form.range === 'time'" v-model="dateRange" type="daterange" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" />
          </div>
        </section>

        <section class="panel block">
          <h3>导出格式</h3>
          <div class="format-grid">
            <button v-for="item in formats" :key="item.value" :class="{ active: form.format === item.value }" @click="form.format = item.value">
              <Document />
              {{ item.label }}
            </button>
          </div>
        </section>
        <el-button class="download-action" type="primary" size="large" :loading="loading" @click="download">生成并下载</el-button>
      </div>
      <section class="panel preview">
        <h3>导出内容预览</h3>
        <pre>{{ preview }}</pre>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { exportQuestions } from '@/api/export'
import { getSubjects } from '@/api/question'

const route = useRoute()
const ranges = [
  { label: '当前筛选', value: 'current' },
  { label: '错题本', value: 'wrong' },
  { label: '整批联卷', value: 'batch' },
  { label: '指定知识点', value: 'knowledge' },
  { label: '掌握状态', value: 'mastery' },
  { label: '指定任务', value: 'task' },
  { label: '时间范围', value: 'time' }
]
const formats = [
  { label: 'Markdown', value: 'markdown' },
  { label: 'Word', value: 'word' },
  { label: 'PDF', value: 'pdf' }
]
const loading = ref(false)
const subjects = ref(['数学', '英语', '计算机', '政治', '专业课', '物理'])
const dateRange = ref([])
const form = reactive({
  range: route.query.range || 'current',
  format: 'markdown',
  keyword: route.query.keyword || '',
  subject: route.query.subject || '',
  questionType: route.query.questionType || '',
  difficulty: route.query.difficulty || '',
  taskId: route.query.taskId || '',
  batchId: route.query.batchId || '',
  knowledgePoint: route.query.knowledgePoint || '',
  masteryStatus: route.query.masteryStatus || ''
})

const preview = computed(() => `# SnapMatch 题目整理导出

> 导出时间：${new Date().toLocaleString()}
> 范围：${ranges.find((item) => item.value === form.range)?.label}
> 格式：${form.format.toUpperCase()}

## 题目 1 · 示例题
- 科目：数学
- 知识点：导数 / 函数求导

### 题干
完整题干、选项和公式会保留。

### OCR 识别文本
通义 OCR 识别文本会随题目一起导出。

### VLM 解析
- 答案：答案作为解析内容的一部分展示
- 解析摘要：保留模型返回的摘要、步骤、常见错误、复习计划和相似练习建议。`)

async function loadSubjects() {
  const res = await getSubjects()
  subjects.value = (res.data || []).map((item) => item.name || item).filter(Boolean)
}

async function download() {
  loading.value = true
  try {
    const [startTime, endTime] = dateRange.value || []
    await exportQuestions({ ...form, startTime, endTime })
    ElMessage.success('导出文件已生成')
  } finally {
    loading.value = false
  }
}

onMounted(loadSubjects)
</script>

<style scoped>
.export-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.85fr;
  gap: 22px;
}

.block,
.preview {
  padding: 22px;
  margin-bottom: 18px;
}

.block h3,
.preview h3 {
  margin: 0 0 14px;
  font-size: 16px;
}

.choice-grid,
.format-grid,
.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.format-grid {
  grid-template-columns: repeat(3, 1fr);
}

.choice-grid button,
.format-grid button {
  min-height: 50px;
  border: 1px solid var(--sm-border);
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
}

.choice-grid button.active,
.format-grid button.active {
  border-color: var(--sm-primary);
  color: var(--sm-primary);
  background: #f1f5ff;
}

.format-grid button svg {
  width: 24px;
}

.download-action {
  width: 100%;
  height: 44px;
}

pre {
  overflow: auto;
  max-height: 420px;
  padding: 18px;
  border-radius: 12px;
  color: var(--sm-text-2);
  background: #f8fafc;
  line-height: 1.65;
  white-space: pre-wrap;
}

@media (max-width: 900px) {
  .export-grid,
  .choice-grid,
  .format-grid,
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
