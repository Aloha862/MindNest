<template>
  <section class="panel table-panel">
    <div class="filter-row">
      <el-input v-model="localKeyword" class="soft-input" :placeholder="placeholder" :prefix-icon="Search" clearable @input="$emit('search', localKeyword)" />
      <slot name="filters" />
    </div>
    <div class="table-wrap">
      <el-table v-loading="loading" :data="rows" stripe style="width: 100%">
        <slot />
      </el-table>
    </div>
    <el-empty v-if="!loading && !rows.length" description="暂无数据" />
    <div v-if="total > pageSize" class="table-pager">
      <el-pagination
        background
        layout="prev, pager, next"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="$emit('page-change', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

defineEmits(['search', 'page-change'])
defineProps({
  rows: { type: Array, default: () => [] },
  placeholder: { type: String, default: '搜索关键词' },
  loading: { type: Boolean, default: false },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 }
})

const localKeyword = ref('')
</script>

<style scoped>
.table-wrap {
  overflow-x: auto;
}

:deep(.el-select) {
  width: 150px;
}

.table-pager {
  display: flex;
  justify-content: center;
  margin-top: 18px;
}
</style>
