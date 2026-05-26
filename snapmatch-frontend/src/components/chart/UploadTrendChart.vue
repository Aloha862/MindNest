<template>
  <BaseChart :option="option" />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'

const props = defineProps({ data: { type: Array, default: () => [] } })
const option = computed(() => ({
  grid: { left: 36, right: 12, top: 20, bottom: 32 },
  xAxis: { type: 'category', data: props.data.map((item) => item.date), boundaryGap: false, axisLine: { lineStyle: { color: '#cbd5e1' } } },
  yAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf2f7', type: 'dashed' } } },
  series: [{ type: 'line', smooth: true, data: props.data.map((item) => item.value), symbolSize: 9, lineStyle: { width: 3, color: '#4f7fe8' }, itemStyle: { color: '#4f7fe8' } }]
}))
</script>
