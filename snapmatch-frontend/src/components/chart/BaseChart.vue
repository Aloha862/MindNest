<template>
  <div ref="chartRef" class="chart" />
</template>

<script setup>
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  option: { type: Object, required: true }
})

const chartRef = ref(null)
let instance = null

function render() {
  if (!chartRef.value) return
  if (!instance) instance = echarts.init(chartRef.value)
  instance.setOption(props.option, true)
}

onMounted(() => {
  render()
  window.addEventListener('resize', render)
})

watch(() => props.option, render, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', render)
  instance?.dispose()
})
</script>

<style scoped>
.chart {
  width: 100%;
  height: 260px;
}
</style>
