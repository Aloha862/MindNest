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

      <h2>{{ question.title || bodyText || '题目详情' }}</h2>
      <div v-if="question.knowledgePoints?.length" class="tag-row">
        <el-tag v-for="point in question.knowledgePoints" :key="point" size="small" effect="plain">{{ point }}</el-tag>
      </div>

      <small>题目正文</small>
      <div class="soft plain-text">
        {{ bodyText || '暂无纯文本题目正文，公式内容请查看 VLM 完整解析。' }}
      </div>

      <div v-if="plainOptions.length" class="option-list">
        <strong>选项</strong>
        <p v-for="option in plainOptions" :key="option">
          {{ option }}
        </p>
      </div>
    </article>

    <article class="panel block">
      <small>OCR 识别文本</small>
      <div class="soft ocr-text">
        <MathText :text="ocrDisplayText || '暂无 OCR 文本'" />
      </div>
    </article>

    <article class="panel block ai">
      <small>VLM 完整解析</small>

      <section v-if="vlmStem" class="section-list">
        <strong>题干</strong>
        <div class="soft">
          <MathText :text="vlmStem" />
        </div>
      </section>

      <section v-if="vlmOptions.length" class="section-list">
        <strong>选项</strong>
        <div class="option-list vlm-options">
          <p v-for="option in vlmOptions" :key="option.key">
            <MathText :text="option.text" compact />
          </p>
        </div>
      </section>

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

      <section v-if="vlmFormulas.length" class="section-list formula-list">
        <strong>公式</strong>
        <span v-for="formula in vlmFormulas" :key="formula.key" class="formula-item">
          <MathText :text="`$$${formula.latex}$$`" compact />
          <small v-if="formula.description">{{ formula.description }}</small>
        </span>
      </section>

      <section v-if="vlm.detailedAnalysis || question.detailedAnalysis">
        <strong>详细解析</strong>
        <div class="soft">
          <MathText :text="vlm.detailedAnalysis || question.detailedAnalysis" />
        </div>
      </section>

      <SectionList title="解题步骤" :items="vlm.solutionSteps || question.solutionSteps" />
      <SectionList title="常见错误" :items="vlm.commonMistakes || question.commonMistakes" />
      <SectionList title="错误原因" :items="vlm.errorCauseTags || question.errorCauseTags" tag />
      <SectionList title="复习计划" :items="vlm.reviewPlan || question.reviewPlan" />
      <SectionList title="相似练习建议" :items="vlm.similarPracticeSuggestions || question.similarPracticeSuggestions" />
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

const bodyText = computed(() => stripMath(props.question.content || props.question.stem || ''))
const ocrDisplayText = computed(() => props.question.ocrText || props.question.content || '')
const plainOptions = computed(() => (props.question.options || [])
  .map((option, index) => stripMath(optionText(option, index)))
  .filter(Boolean))
const vlmStem = computed(() => vlm.value.stem || vlm.value.content || props.question.rawVlmJson?.stem || props.question.rawVlmJson?.content || props.question.content || '')
const vlmOptions = computed(() => {
  const options = vlm.value.options?.length ? vlm.value.options : (props.question.options || [])
  return options
    .map((option, index) => ({
      key: `${index}-${optionText(option, index)}`,
      text: optionText(option, index)
    }))
    .filter((option) => option.text)
})

const vlmFormulas = computed(() => {
  const formulas = vlm.value.formulas?.length ? vlm.value.formulas : (props.question.formulas || [])
  return formulas
    .map((formula, index) => {
      const latex = inlineLatex(formulaText(formula))
      return {
        key: `${index}-${latex}`,
        latex,
        description: typeof formula === 'object' ? (formula.description || formula.source || '') : ''
      }
    })
    .filter((formula) => formula.latex)
})

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

function stripMath(value) {
  return String(value || '')
    .replace(/\$\$[\s\S]*?\$\$/g, ' ')
    .replace(/\$[^$\n]*\$/g, ' ')
    .replace(/\\\[[\s\S]*?\\\]/g, ' ')
    .replace(/\\\([\s\S]*?\\\)/g, ' ')
    .replace(/\\[a-zA-Z]+(?:\s*[_^]\{[^}]*\})?(?:\s*\{[^}]*\})*/g, ' ')
    .replace(/[{}_^|]+/g, ' ')
    .replace(/[ \t]+/g, ' ')
    .replace(/\s+([，。；、,.;!?！？])/g, '$1')
    .replace(/([，。；、,.;!?！？])\s+/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
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

.plain-text {
  white-space: pre-wrap;
  color: var(--sm-text);
}

.mono {
  white-space: pre-wrap;
}

.ocr-text :deep(.math-line) {
  margin: 0;
}

.ocr-text :deep(.math-line + .math-line) {
  margin-top: 8px;
}

.ocr-text :deep(.math-inline) {
  max-width: none;
  overflow: visible;
  white-space: nowrap;
  vertical-align: middle;
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

.vlm-options {
  margin-top: 0;
}

.formula-list {
  justify-items: start;
}

.formula-item {
  display: block;
  width: 100%;
  max-width: 100%;
  padding: 8px 10px;
  overflow: hidden;
  border: 1px solid var(--sm-border);
  border-radius: 8px;
  background: #fff;
  color: var(--sm-text);
}

.formula-item small {
  margin-top: 6px;
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
