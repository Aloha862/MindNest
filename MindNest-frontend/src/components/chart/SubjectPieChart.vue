<template>
  <BaseChart :option="option" />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'

const props = defineProps({ data: { type: Array, default: () => [] } })
const colors = ['#3b82f6', '#22c55e', '#ef4444', '#f59e0b', '#8b5cf6', '#4fb5d3']
const option = computed(() => ({
  color: colors,
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, left: 0, itemWidth: 8, itemHeight: 8 },
  series: [{ type: 'pie', radius: ['48%', '72%'], center: ['50%', '42%'], label: { show: false }, data: props.data }]
}))
</script>
