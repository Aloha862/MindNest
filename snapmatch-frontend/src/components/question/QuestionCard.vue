<template>
  <article class="question-card panel" @click="openDetail">
    <div class="badges">
      <el-tag size="small" effect="plain">{{ question.subject }}</el-tag>
      <el-tag size="small" effect="plain">{{ question.questionType }}</el-tag>
      <el-tag size="small" :type="difficultyType(question.difficulty)" effect="light">{{ question.difficulty }}</el-tag>
    </div>
    <h3>{{ question.title }}</h3>
    <div class="content-preview">
      <MathText :text="question.content" compact />
    </div>
    <TagGroup :tags="question.knowledgePoints" />
    <footer>
      <span>{{ safeDate(question.createdAt).slice(0, 10) }}</span>
      <span class="icons">
        <StarFilled v-if="question.isWrong" class="wrong-mark" />
        <Star v-else-if="wrongable" title="加入错题本" @click.stop="$emit('wrong', question)" />
        <Picture />
        <Delete v-if="deletable" @click.stop="$emit('delete', question)" />
      </span>
    </footer>
  </article>
</template>

<script setup>
import { Delete, Picture, Star, StarFilled } from '@element-plus/icons-vue'
import { useRoute, useRouter } from 'vue-router'
import { difficultyType, safeDate } from '@/utils/format'
import MathText from '@/components/common/MathText.vue'
import TagGroup from './TagGroup.vue'

const props = defineProps({
  question: { type: Object, required: true },
  deletable: { type: Boolean, default: true },
  wrongable: { type: Boolean, default: false }
})
defineEmits(['delete', 'wrong'])

const router = useRouter()
const route = useRoute()

function openDetail() {
  const prefix = route.path.startsWith('/admin') ? '/admin/questions' : '/user/questions'
  router.push(`${prefix}/${props.question.id}`)
}
</script>

<style scoped>
.question-card {
  display: flex;
  height: 260px;
  min-height: 260px;
  max-height: 260px;
  flex-direction: column;
  padding: 18px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.question-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.09);
}

.badges {
  display: flex;
  min-height: 24px;
  gap: 8px;
  overflow: hidden;
  white-space: nowrap;
}

.badges :deep(.el-tag) {
  max-width: 96px;
  flex: 0 1 auto;
}

.badges :deep(.el-tag__content) {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
}

h3 {
  margin: 14px 0 8px;
  min-height: 44px;
  max-height: 44px;
  overflow: hidden;
  display: -webkit-box;
  font-size: 17px;
  line-height: 1.3;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.content-preview {
  max-height: 74px;
  min-height: 74px;
  margin: 0 0 12px;
  overflow: hidden;
  color: var(--sm-muted);
  line-height: 1.55;
}

.content-preview :deep(.math-text) {
  max-height: 74px;
  overflow: hidden;
}

.content-preview :deep(.math-line) {
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-card :deep(.tag-group) {
  max-height: 26px;
  min-height: 26px;
  overflow: hidden;
  flex-wrap: nowrap;
}

.question-card :deep(.tag-group span) {
  max-width: 96px;
  flex: 0 0 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 35px;
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--sm-border);
  color: var(--sm-muted);
}

.icons {
  display: inline-flex;
  gap: 12px;
}

.icons svg {
  cursor: pointer;
}

.wrong-mark {
  color: #f59e0b;
}
</style>
