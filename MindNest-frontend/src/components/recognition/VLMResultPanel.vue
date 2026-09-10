<template>
  <section class="panel result-panel ai">
    <header class="panel-head">
      <div>
        <h3>VLM 结构化分析</h3>
        <p>题干、选项、答案、解析、知识点与复习建议</p>
      </div>
      <span>{{ result.questions?.length || 0 }} 题</span>
    </header>

    <el-skeleton v-if="pending" :rows="6" animated />

    <template v-else>
      <el-alert
        v-if="result.needsReview || result.validationWarnings?.length"
        class="review-alert"
        type="warning"
        :closable="false"
        :title="reviewMessage"
      />

      <div class="summary">
        <MathText :text="result.summary || '暂无结构化分析摘要'" />
      </div>

      <div class="question-stack">
        <article v-for="item in richQuestions" :key="item.id || item.title" class="question-analysis">
          <header>
            <div>
              <strong>{{ item.title || '未命名题目' }}</strong>
              <span>{{ item.subject }} · {{ item.questionType }} · {{ item.difficulty }} · {{ item.chapter || '未归属章节' }}</span>
            </div>
            <em v-if="item.answer">
              答案：<MathText :text="item.answer" compact inline />
            </em>
          </header>

          <div class="stem">
            <MathText :text="item.stem || item.content" />
          </div>

          <div v-if="item.options?.length" class="options">
            <div v-for="option in item.options" :key="optionText(option)">
              <MathText :text="optionText(option)" compact />
            </div>
          </div>

          <section class="block">
            <h4>公式</h4>
            <div v-if="item.renderedFormulas.length" class="formula-list">
              <div v-for="formula in item.renderedFormulas" :key="formula.key" class="formula">
                <MathText :text="`$$${formula.latex}$$`" compact />
                <small v-if="formula.description">{{ formula.description }}</small>
              </div>
            </div>
            <p v-else class="empty-text">无</p>
          </section>

          <section v-if="item.detailedAnalysis || item.analysisSummary" class="block">
            <h4>解析</h4>
            <MathText :text="item.detailedAnalysis || item.analysisSummary" />
          </section>

          <section v-if="item.solutionSteps?.length" class="block">
            <h4>解题步骤</h4>
            <ol>
              <li v-for="step in item.solutionSteps" :key="itemText(step)">
                <MathText :text="itemText(step)" compact />
              </li>
            </ol>
          </section>

          <section class="insight-grid">
            <div v-if="item.commonMistakes?.length">
              <h4>常见错误</h4>
              <ul>
                <li v-for="mistake in item.commonMistakes" :key="itemText(mistake)">
                  <MathText :text="itemText(mistake)" compact />
                </li>
              </ul>
            </div>
            <div v-if="item.errorCauseTags?.length">
              <h4>错误原因</h4>
              <TagGroup :tags="item.errorCauseTags" />
            </div>
            <div v-if="item.reviewPlan?.length">
              <h4>复习计划</h4>
              <ul>
                <li v-for="plan in item.reviewPlan" :key="itemText(plan)">
                  <MathText :text="itemText(plan)" compact />
                </li>
              </ul>
            </div>
            <div v-if="item.similarPracticeSuggestions?.length">
              <h4>相似练习</h4>
              <ul>
                <li v-for="suggestion in item.similarPracticeSuggestions" :key="itemText(suggestion)">
                  <MathText :text="itemText(suggestion)" compact />
                </li>
              </ul>
            </div>
          </section>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import MathText from '@/components/common/MathText.vue'
import TagGroup from '@/components/question/TagGroup.vue'

const props = defineProps({
  result: { type: Object, required: true },
  pending: { type: Boolean, default: false }
})

function itemText(item) {
  return String(typeof item === 'object' ? (item.text || item.content || item.title || JSON.stringify(item)) : item)
}

function optionText(option) {
  if (typeof option === 'string') return option
  const label = option?.label || option?.key || ''
  const text = option?.text || option?.content || ''
  return `${label ? `${label}. ` : ''}${text}`.trim()
}

function cleanLatex(value) {
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

const richQuestions = computed(() =>
  (props.result.questions || []).map((item) => ({
    ...item,
    renderedFormulas: (item.formulas || [])
      .map((formula, index) => ({
        key: `${index}-${formula?.latex || formula?.text || formula}`,
        latex: cleanLatex(formula?.latex || formula?.text || formula),
        description: formula?.description || ''
      }))
      .filter((formula) => formula.latex)
  }))
)

const reviewMessage = computed(() => {
  const warnings = props.result.validationWarnings || []
  return warnings.length ? warnings.join('；') : '部分字段由系统补全，建议人工复核'
})
</script>

<style scoped>
.result-panel {
  padding: 22px;
}

.ai {
  border-color: #ddd6fe;
  background: #f7f5ff;
}

.panel-head,
.question-analysis header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

h3,
h4,
p {
  margin: 0;
}

.panel-head p,
.question-analysis header span {
  margin-top: 6px;
  color: var(--sm-muted);
  font-size: 13px;
}

.panel-head > span,
.question-analysis em {
  flex: none;
  padding: 5px 10px;
  border-radius: 999px;
  color: #6d28d9;
  background: #ede9fe;
  font-size: 12px;
  font-style: normal;
}

.question-analysis em {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.summary {
  padding: 14px;
  border-radius: 12px;
  color: var(--sm-text-2);
  background: rgba(255, 255, 255, 0.72);
}

.review-alert {
  margin-bottom: 14px;
}

.question-stack {
  display: grid;
  gap: 14px;
  margin-top: 14px;
}

.question-analysis {
  display: grid;
  gap: 14px;
  padding: 16px;
  border: 1px solid #e9d5ff;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
}

.stem {
  color: var(--sm-text-2);
}

.options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.options div {
  padding: 10px;
  border-radius: 10px;
  background: #f8fafc;
  color: var(--sm-text-2);
}

.block {
  display: grid;
  gap: 10px;
  color: var(--sm-text-2);
}

.formula-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.formula {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--sm-border);
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.formula small {
  flex: none;
  min-width: max-content;
  margin-top: 0;
  color: var(--sm-muted);
}

.empty-text {
  padding: 12px;
  border-radius: 10px;
  color: var(--sm-muted);
  background: #f8fafc;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.insight-grid > div {
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
}

.insight-grid h4 {
  margin-bottom: 8px;
}

.insight-grid li {
  color: var(--sm-text-2);
}

ol,
ul {
  margin: 0;
  padding-left: 20px;
}

@media (max-width: 760px) {
  .options,
  .insight-grid {
    grid-template-columns: 1fr;
  }
}
</style>
