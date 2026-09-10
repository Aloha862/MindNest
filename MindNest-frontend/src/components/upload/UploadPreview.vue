<template>
  <section class="panel upload-preview">
    <h3>上传队列</h3>
    <p v-if="!items.length">未选择文件</p>
    <ul v-else>
      <li v-for="(item, index) in items" :key="`${item.name}-${index}`">
        <div>
          <strong>{{ item.name }}</strong>
          <span>{{ fileSizeText(item.size) }} · {{ item.type || 'image' }}</span>
        </div>
        <el-tag size="small" :type="item.status === 'failed' ? 'danger' : item.status === 'uploaded' ? 'success' : 'info'">
          {{ item.statusText || statusText(item.status) }}
        </el-tag>
        <button v-if="removable" class="remove" type="button" @click="$emit('remove', index)">移除</button>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { fileSizeText } from '@/utils/file'

const props = defineProps({
  file: { type: Object, default: null },
  files: { type: Array, default: () => [] },
  removable: { type: Boolean, default: false }
})
defineEmits(['remove'])

const items = computed(() => props.files.length ? props.files : (props.file ? [props.file] : []))

function statusText(status) {
  return ({ local: '本地待上传', uploading: '上传中', uploaded: '已上传', failed: '失败' })[status] || '本地待上传'
}
</script>

<style scoped>
.upload-preview {
  padding: 20px;
}

h3 {
  margin-top: 0;
}

p,
span {
  color: var(--sm-muted);
}

ul {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 10px;
  align-items: center;
  padding: 10px;
  border: 1px solid var(--sm-border);
  border-radius: 10px;
}

strong {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove {
  border: 0;
  background: transparent;
  color: #ef4444;
  cursor: pointer;
}
</style>
