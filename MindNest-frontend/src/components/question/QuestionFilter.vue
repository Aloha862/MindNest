<template>
  <section class="panel filter-card">
    <el-input v-model="query.keyword" class="soft-input" placeholder="搜索题目标题或内容" :prefix-icon="Search" clearable />
    <el-select v-model="query.subject" placeholder="全部科目" clearable>
      <el-option v-for="item in subjects" :key="item" :label="item" :value="item" />
    </el-select>
    <el-select v-model="query.questionType" placeholder="全部题型" clearable>
      <el-option v-for="item in types" :key="item" :label="item" :value="item" />
    </el-select>
    <el-select v-model="query.difficulty" placeholder="全部难度" clearable>
      <el-option v-for="item in difficulties" :key="item" :label="item" :value="item" />
    </el-select>
    <el-button @click="$emit('reset')">重置</el-button>
  </section>
</template>

<script setup>
import { Search } from '@element-plus/icons-vue'

defineEmits(['reset'])
defineProps({
  query: { type: Object, required: true },
  subjects: { type: Array, default: () => ['数学', '英语', '计算机', '政治', '专业课', '物理'] }
})

const types = ['选择题', '填空题', '简答题', '计算题', '阅读理解']
const difficulties = ['基础', '进阶', '挑战']
</script>

<style scoped>
.filter-card {
  display: grid;
  grid-template-columns: 1fr 130px 130px 130px 80px;
  gap: 12px;
  padding: 16px;
}

@media (max-width: 860px) {
  .filter-card {
    grid-template-columns: 1fr;
  }
}
</style>
