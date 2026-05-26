<template>
  <section class="detail-stack">
    <article class="panel block">
      <div class="badges">
        <el-tag size="small">{{ question.subject || '未分类' }}</el-tag>
        <el-tag size="small">{{ question.questionType || '未知题型' }}</el-tag>
        <el-tag size="small" :type="difficultyType(question.difficulty)">{{ question.difficulty || '未标注' }}</el-tag>
        <el-tag v-if="question.reviewStatus === 'pending'" size="small" type="warning">待复核</el-tag>
        <el-tag v-if="question.confidence" size="small" :type="question.confidence < 0.65 ? 'warning' : 'success'">
          置信度 {{ Number(question.confidence).toFixed(2) }}
        </el-tag>
      </div>

      <h2>{{ question.title }}</h2>
      <div class="tag-row">
        <el-tag v-for="point in question.knowledgePoints || []" :key="point" size="small" effect="plain">{{ point }}</el-tag>
      </div>

      <small>题目正文</small>
      <div class="soft">
        <MathText :text="question.content" />
      </div>

      <div v-if="question.options?.length" class="option-list">
        <strong>选项</strong>
        <p v-for="(option, index) in question.options" :key="index">
          {{ optionText(option, index) }}
        </p>
      </div>

      <div v-if="question.formulas?.length" class="formula-list">
        <strong>公式</strong>
        <span v-for="(formula, index) in question.formulas" :key="index" class="formula-item">
          <MathText :text="`$$${inlineLatex(formulaText(formula))}$$`" compact />
        </span>
      </div>
    </article>

    <article class="panel block">
      <small>OCR 识别文本</small>
      <div class="soft mono">
        <MathText :text="question.ocrText || question.content" />
      </div>

      <div v-if="question.formulaBlocks?.length" class="formula-list">
        <strong>公式块</strong>
        <span v-for="(formula, index) in question.formulaBlocks" :key="index" class="formula-item">
          <MathText :text="`$$${inlineLatex(formulaText(formula))}$$`" compact />
        </span>
      </div>
    </article>

    <article class="panel block ai">
      <small>VLM 完整解析</small>
      <div class="analysis-grid">
        <section>
          <strong>答案</strong>
          <div class="soft">
            <MathText :text="vlm.answer || question.answer || '暂无答案'" />
          </div>
        </section>
        <section>
          <strong>解析摘要</strong>
          <div class="soft">
            <MathText :text="vlm.analysisSummary || question.analysisSummary || '暂无解析摘要'" />
          </div>
        </section>
      </div>

      <section v-if="vlm.detailedAnalysis || question.detailedAnalysis">
        <strong>详细解析</strong>
        <div class="soft">
          <MathText :text="vlm.detailedAnalysis || question.detailedAnalysis" />
        </div>
      </section>

      <section-list title="解题步骤" :items="vlm.solutionSteps || question.solutionSteps" />
      <section-list title="常见错误" :items="vlm.commonMistakes || question.commonMistakes" />
      <section-list title="错误原因" :items="vlm.errorCauseTags || question.errorCauseTags" tag />
      <section-list title="复习计划" :items="vlm.reviewPlan || question.reviewPlan" />
      <section-list title="相似练习建议" :items="vlm.similarPracticeSuggestions || question.similarPracticeSuggestions" />
      <p v-if="vlm.estimatedTime || question.estimatedTime" class="estimate">预计用时：{{ vlm.estimatedTime || question.estimatedTime }}</p>
    </article>
  </section>
</template>

<script setup>
import { computed, defineComponent, h } from 'vue'
import MathText from '@/components/common/MathText.vue'
import { difficultyType } from '@/utils/format'

const props = defineProps({ question: { type: Object, required: true } })
const vlm = computed(() => props.question.vlmDetail || props.question.rawVlmJson || {})

function optionText(option, index) {
  if (typeof option === 'string') return option
  const label = option?.label || option?.key || String.fromCharCode(65 + index)
  const text = option?.text || option?.content || ''
  return `${label}. ${text}`.trim()
}

function formulaText(formula) {
  if (typeof formula === 'string') return formula
  return formula?.latex || formula?.text || formula?.content || JSON.stringify(formula)
}

function inlineLatex(value) {
  let text = String(value || '').replace(/\s+/g, ' ').trim()
  const inlineMatch = text.match(/\\\(([\s\S]+?)\\\)/) || text.match(/\\\[([\s\S]+?)\\\]/) || text.match(/\$\$?([\s\S]+?)\$\$?/)
  if (inlineMatch) text = inlineMatch[1]
  return text
    .replace(/^\$+|\$+$/g, '')
    .replace(/\\{2,}(?=[A-Za-z])/g, '\\')
    .replace(/\\{2,}\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function itemText(item) {
  return String(typeof item === 'object' ? (item.text || item.content || item.title || JSON.stringify(item)) : item)
}

const SectionList = defineComponent({
  name: 'SectionList',
  props: {
    title: { type: String, required: true },
    items: { type: [Array, String], default: () => [] },
    tag: { type: Boolean, default: false }
  },
  setup(sectionProps) {
    return () => {
      const items = Array.isArray(sectionProps.items) ? sectionProps.items : (sectionProps.items ? [sectionProps.items] : [])
      if (!items.length) return null
      return h('section', { class: 'section-list' }, [
        h('strong', sectionProps.title),
        sectionProps.tag
          ? h('div', { class: 'tag-row' }, items.map((item) => h('span', { class: 'mini-tag' }, [h(MathText, { text: itemText(item), compact: true, inline: true })])))
          : h('ol', items.map((item) => h('li', [h(MathText, { text: itemText(item), compact: true })])))
      ])
    }
  }
})
</script>

<style scoped>
.detail-stack {
  display: grid;
  gap: 18px;
}

.block {
  padding: 22px;
}

.badges,
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

h2 {
  margin: 14px 0 12px;
}

small {
  display: block;
  margin-top: 14px;
  color: var(--sm-muted);
}

.soft {
  margin-top: 10px;
  padding: 16px;
  border: 1px solid var(--sm-border);
  border-radius: 10px;
  background: #fff;
  line-height: 1.7;
}

.mono {
  white-space: pre-wrap;
}

.option-list,
.formula-list,
.section-list {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.option-list p {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid var(--sm-border);
  border-radius: 8px;
  background: #fff;
}

.formula-list {
  justify-items: start;
}

.formula-item {
  display: block;
  width: 100%;
  max-width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--sm-border);
  border-radius: 8px;
  background: #fff;
  color: var(--sm-text);
  overflow: hidden;
}

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.ai {
  border-color: var(--sm-border);
  background: #fff;
}

ol {
  margin: 0;
  padding-left: 22px;
}

li {
  margin: 6px 0;
}

.mini-tag {
  display: inline-flex;
  padding: 4px 8px;
  border-radius: 999px;
  color: #92400e;
  background: #fffbeb;
}

.estimate {
  margin-bottom: 0;
  color: var(--sm-muted);
}

@media (max-width: 900px) {
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style>
