<template>
  <label
    class="uploader"
    :class="{ hasFile: hasFile, dragOver }"
    @dragover.prevent="dragOver = true"
    @dragleave.prevent="dragOver = false"
    @drop.prevent="onDrop"
  >
    <input type="file" accept="image/png,image/jpeg,image/jpg" :multiple="multiple" @change="onChange" />
    <div v-if="previews.length" class="preview-grid">
      <img v-for="item in previews.slice(0, 4)" :key="item" :src="item" alt="上传预览" />
      <strong v-if="previews.length > 4">+{{ previews.length - 4 }}</strong>
    </div>
    <template v-else>
      <span><UploadCloud /></span>
      <strong>拖拽图片到此处，或点击选择文件</strong>
      <p>支持 JPG / PNG，单图或批量联卷上传</p>
      <em><ImagePlus />选择图片</em>
    </template>
  </label>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ImagePlus, UploadCloud } from 'lucide-vue-next'

const props = defineProps({
  preview: { type: String, default: '' },
  previews: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: false }
})
const emit = defineEmits(['select'])
const dragOver = ref(false)
const previewList = computed(() => props.previews.length ? props.previews : (props.preview ? [props.preview] : []))
const previews = previewList
const hasFile = computed(() => previewList.value.length > 0)

function emitFiles(fileList) {
  const files = Array.from(fileList || [])
  if (!files.length) return
  emit('select', props.multiple ? files : files[0])
}

function onChange(event) {
  emitFiles(event.target.files)
  event.target.value = ''
}

function onDrop(event) {
  dragOver.value = false
  emitFiles(event.dataTransfer.files)
}
</script>

<style scoped>
.uploader {
  display: grid;
  place-items: center;
  min-height: 360px;
  border: 2px dashed #d8dfea;
  border-radius: 20px;
  background: #fff;
  cursor: pointer;
  overflow: hidden;
  text-align: center;
  transition: border-color 0.18s ease, background 0.18s ease;
}

.uploader:hover,
.dragOver {
  border-color: rgba(59, 130, 246, 0.7);
  background: rgba(238, 242, 255, 0.45);
}

input {
  display: none;
}

span {
  display: inline-grid;
  place-items: center;
  width: 64px;
  height: 64px;
  margin-bottom: 18px;
  border-radius: 18px;
  color: #fff;
  background: linear-gradient(135deg, var(--sm-primary), var(--sm-ai));
}

svg {
  width: 24px;
  height: 24px;
}

strong {
  display: block;
  font-size: 17px;
  font-weight: 600;
}

p {
  color: var(--sm-muted);
}

em {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  padding: 9px 14px;
  border: 1px solid var(--sm-border);
  border-radius: 10px;
  background: #fff;
  font-style: normal;
  font-weight: 600;
}

.preview-grid {
  display: grid;
  width: 100%;
  min-height: 360px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 10px;
  background: rgba(238, 242, 255, 0.35);
}

.preview-grid img {
  width: 100%;
  height: 168px;
  object-fit: contain;
  border-radius: 10px;
  background: #fff;
}

.preview-grid strong {
  display: grid;
  place-items: center;
  min-height: 168px;
  border-radius: 10px;
  background: #eef2ff;
  color: var(--sm-primary);
}
</style>
