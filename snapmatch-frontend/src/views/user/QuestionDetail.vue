<template>
  <main class="page-shell detail-page">
    <PageHeader v-if="question" title="题目详情" :subtitle="`#${question.id} · ${question.subject} · ${question.questionType}`">
      <el-button @click="$router.back()"><Back />返回</el-button>
      <el-button v-if="!question.isWrong" type="warning" plain @click="addWrong"><Star />加入错题本</el-button>
      <el-button v-else type="success" plain disabled><StarFilled />已在错题本</el-button>
      <el-button type="danger" plain @click="removeQuestion"><Delete />删除</el-button>
    </PageHeader>

    <section v-if="loading" class="panel skeleton">
      <el-skeleton :rows="8" animated />
    </section>

    <section v-else-if="question" class="detail-grid">
      <QuestionDetailPanel :question="question" />
      <aside>
        <section class="panel source">
          <h3>来源图片</h3>
          <div class="image-frame">
            <img v-if="question.sourceImageUrl" :src="question.sourceImageUrl" alt="来源图片" />
            <el-empty v-else description="暂无来源图片" />
          </div>
          <el-button v-if="question.taskId" @click="$router.push(`/user/recognition/${question.taskId}`)">查看识别任务</el-button>
        </section>
        <section class="panel meta">
          <h3>元信息</h3>
          <p><span>题目 ID</span>{{ question.id }}</p>
          <p><span>来源文件</span>{{ question.fileName || question.fileId || '暂无' }}</p>
          <p><span>任务状态</span><StatusTag :status="question.taskStatus || question.reviewStatus" /></p>
          <p><span>复核状态</span>{{ question.reviewStatus || 'approved' }}</p>
          <p><span>创建时间</span>{{ question.createdAt }}</p>
          <p><span>更新时间</span>{{ question.updatedAt }}</p>
        </section>
      </aside>
    </section>

    <el-empty v-else description="未找到题目" />
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Back, Delete, Star, StarFilled } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import QuestionDetailPanel from '@/components/question/QuestionDetailPanel.vue'
import { deleteQuestion, getQuestionDetail, markQuestionWrong } from '@/api/question'

const route = useRoute()
const router = useRouter()
const question = ref(null)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    question.value = (await getQuestionDetail(route.params.id)).data
  } finally {
    loading.value = false
  }
}

async function addWrong() {
  await markQuestionWrong(question.value.id, { source: '题目详情页' })
  await load()
  ElMessage.success('已加入错题本')
}

async function removeQuestion() {
  await ElMessageBox.confirm(`确认删除题目「${question.value.title}」？`, '删除确认', { type: 'warning' })
  await deleteQuestion(question.value.id)
  ElMessage.success('题目已删除')
  router.push('/user/questions')
}

onMounted(load)
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) 360px;
  gap: 20px;
}

.skeleton {
  padding: 24px;
}

aside {
  display: grid;
  gap: 18px;
  align-content: start;
}

.source,
.meta {
  padding: 20px;
}

.image-frame {
  display: grid;
  place-items: center;
  min-height: 260px;
  border-radius: 12px;
  background: #f8fafc;
}

.source img {
  width: 100%;
  max-height: 420px;
  object-fit: contain;
}

.source .el-button {
  width: 100%;
  margin-top: 12px;
}

.meta p {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.meta span {
  color: var(--sm-muted);
}

@media (max-width: 960px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
