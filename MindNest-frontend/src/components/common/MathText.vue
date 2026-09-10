<template>
  <div ref="containerRef" class="math-text" :class="{ compact, block, inlineMode: inline }">
    <template v-for="(line, lineIndex) in renderedLines" :key="line.key || lineIndex">
      <div v-if="line.type === 'display'" class="math-display">
        <div class="math-display-fit" v-html="line.html" />
      </div>
      <p v-else class="math-line">
        <template v-for="(part, partIndex) in line.parts" :key="`${lineIndex}-${partIndex}`">
          <span v-if="part.type === 'text'">{{ part.value }}</span>
          <span v-else class="math-inline" v-html="part.html" />
        </template>
      </p>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({
  text: { type: [String, Number], default: '' },
  compact: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
  inline: { type: Boolean, default: false }
})

const containerRef = ref(null)
let resizeObserver

const SUPERSCRIPT_MAP = {
  '\u2070': '0', '\u00b9': '1', '\u00b2': '2', '\u00b3': '3', '\u2074': '4',
  '\u2075': '5', '\u2076': '6', '\u2077': '7', '\u2078': '8', '\u2079': '9',
  '\u207a': '+', '\u207b': '-', '\u207f': 'n', '\u02e3': 'x'
}

const SUBSCRIPT_MAP = {
  '\u2080': '0', '\u2081': '1', '\u2082': '2', '\u2083': '3', '\u2084': '4',
  '\u2085': '5', '\u2086': '6', '\u2087': '7', '\u2088': '8', '\u2089': '9',
  '\u208a': '+', '\u208b': '-', '\u2099': 'n'
}

function normalizeScriptChars(value, map, prefix) {
  let result = ''
  let index = 0
  while (index < value.length) {
    if (map[value[index]]) {
      let content = ''
      while (index < value.length && map[value[index]]) {
        content += map[value[index]]
        index += 1
      }
      result += `${prefix}{${content}}`
    } else {
      result += value[index]
      index += 1
    }
  }
  return result
}

function normalizeFunctions(latex) {
  return latex
    .replace(/(^|[^\\])\blim\b/g, '$1\\lim')
    .replace(/(^|[^\\])\bsin\b/g, '$1\\sin')
    .replace(/(^|[^\\])\bcos\b/g, '$1\\cos')
    .replace(/(^|[^\\])\btan\b/g, '$1\\tan')
    .replace(/(^|[^\\])\bln\b/g, '$1\\ln')
    .replace(/(^|[^\\])\barcsin\b/g, '$1\\arcsin')
    .replace(/(^|[^\\])\barccos\b/g, '$1\\arccos')
    .replace(/(^|[^\\])\barctan\b/g, '$1\\arctan')
}

function normalizeSqrt(latex) {
  return latex
    .replace(/\\sqrt\s*\|([^|]+)\|/g, '\\sqrt{|$1|}')
    .replace(/\\sqrt\s*\(([^)]+)\)/g, '\\sqrt{($1)}')
    .replace(/\\sqrt\s*([A-Za-z0-9]+(?:\s*[-+]\s*[A-Za-z0-9^{}]+)?)/g, '\\sqrt{$1}')
}

function normalizeFractions(latex) {
  return latex
    .replace(/1\s*\/\s*(\\sqrt\{[^}]+\})/g, '\\frac{1}{$1}')
    .replace(/dx\s*\/\s*(\\sqrt\{[^}]+\})/g, '\\frac{dx}{$1}')
}

function cleanupFormula(value) {
  return String(value || '')
    .replace(/\r?\n/g, ' ')
    .replace(/\\{2,}(?=[A-Za-z])/g, '\\')
    .replace(/\\{2,}\s*/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/^\$+|\$+$/g, '')
    .trim()
}

function toLatex(value) {
  let latex = cleanupFormula(value)
  latex = latex.replace(/\\{2,}(?=[A-Za-z])/g, '\\')
  latex = latex.replace(/\\{2,}\s*/g, ' ')
  latex = latex.replace(/\\\\([A-Za-z]+)/g, '\\$1')
  latex = latex.replace(/\\\\([()[\]])/g, '\\$1')
  latex = latex.replace(/^\\\(([\s\S]*)\\\)$/g, '$1')
  latex = latex.replace(/^\\\[([\s\S]*)\\\]$/g, '$1')
  latex = normalizeScriptChars(latex, SUBSCRIPT_MAP, '_')
  latex = normalizeScriptChars(latex, SUPERSCRIPT_MAP, '^')

  const replacements = [
    [/\u221e/g, '\\infty'],
    [/\u222b/g, '\\int'],
    [/\u2211/g, '\\sum'],
    [/\u03a3/g, '\\Sigma'],
    [/\u221a/g, '\\sqrt'],
    [/\u03c0/g, '\\pi'],
    [/\u00d7/g, '\\times'],
    [/\u00f7/g, '\\div'],
    [/\u2264/g, '\\le'],
    [/\u2265/g, '\\ge'],
    [/\u2260/g, '\\ne'],
    [/\u2248/g, '\\approx'],
    [/\u2192/g, '\\to'],
    [/\u21d2/g, '\\Rightarrow'],
    [/（/g, '('],
    [/）/g, ')'],
    [/，/g, ',']
  ]
  replacements.forEach(([pattern, replacement]) => {
    latex = latex.replace(pattern, replacement)
  })

  latex = latex.replace(/([A-Za-z0-9)\]])\^(\d+)/g, '$1^{$2}')
  latex = latex.replace(/\^\(([^)]+)\)/g, '^{$1}')
  latex = latex.replace(/_\(([^)]+)\)/g, '_{$1}')
  latex = latex.replace(/\\int_([^\s^{}])\^([^\s{}]+)/g, '\\int_{$1}^{$2}')
  latex = latex.replace(/\\int_\{([^}]+)\}\^\{([^}]+)\}/g, '\\int_{$1}^{$2}')
  latex = normalizeFunctions(latex)
  latex = latex.replace(/\^\{\\(sin|cos|tan|ln|arcsin|arccos|arctan)\s+([^}]+)\}/g, '^{\\$1 $2}')
  latex = normalizeSqrt(latex)
  latex = normalizeFractions(latex)
  return latex
}

function isComplexLatex(value) {
  return /\\(?:frac|dfrac|tfrac|int|sum|prod|lim|sqrt)|\|_\{|\\left|\\right/.test(value)
}

function isMathCandidate(value) {
  const text = String(value || '').trim()
  if (!text || text.length < 2) return false
  if (/^[A-D]\.?$/.test(text)) return false
  return /[=+\-*/^_\\{}[\]\u222b\u221e\u03c0\u221a\u2264\u2265\u2260\u2248\u2192\u21d2\u2080-\u2089\u2070-\u2079\u00b2\u00b3]|[A-Za-z]'?\([^)]*\)|\\[a-zA-Z]+/.test(text)
}

function isMathChar(char) {
  return /[A-Za-z0-9\\()[\]{}.,;:'’\-*/=<>^_| \u222b\u221e\u03c0\u221a\u2264\u2265\u2260\u2248\u2192\u21d2\u2080-\u2089\u2070-\u2079\u00b2\u00b3]/.test(char)
}

function renderMath(value, displayMode = false) {
  const latex = toLatex(value)
  try {
    return katex.renderToString(latex, {
      throwOnError: true,
      displayMode,
      strict: 'ignore'
    })
  } catch {
    return String(value)
  }
}

function parseInlineMath(line) {
  const parts = []
  let index = 0
  let textBuffer = ''

  const pushText = () => {
    if (textBuffer) {
      parts.push({ type: 'text', value: textBuffer })
      textBuffer = ''
    }
  }

  while (index < line.length) {
    if (line[index] === '$') {
      const end = line.indexOf('$', index + 1)
      if (end > index) {
        const candidate = cleanupFormula(line.slice(index + 1, end))
        pushText()
        parts.push({ type: 'math', html: renderMath(candidate) })
        index = end + 1
        continue
      }
    }

    if (!isMathChar(line[index])) {
      textBuffer += line[index]
      index += 1
      continue
    }

    let end = index
    while (end < line.length && isMathChar(line[end])) {
      end += 1
    }
    const raw = line.slice(index, end)
    const candidate = raw.trimEnd()
    const trailingSpaces = raw.slice(candidate.length)
    if (isMathCandidate(candidate)) {
      pushText()
      parts.push({ type: 'math', html: renderMath(candidate) })
      textBuffer += trailingSpaces
    } else {
      textBuffer += raw
    }
    index = end
  }

  pushText()
  return parts.length ? parts : [{ type: 'text', value: line }]
}

function normalizeInput(value) {
  let text = String(value ?? '')
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1')
  text = text.replace(/\\\\([()[\]])/g, '\\$1')
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, formula) => `\n$$${cleanupFormula(formula)}$$\n`)
  text = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, formula) => `\n$$${cleanupFormula(formula)}$$\n`)
  text = text.replace(/\\\(([\s\S]*?)\\\)/g, (_, formula) => `$${cleanupFormula(formula)}$`)
  return text
}

function isDisplayFormulaLine(line) {
  return /^\s*\$\$[\s\S]*\$\$\s*$/.test(line)
}

const renderedLines = computed(() => {
  let value = normalizeInput(props.text)
  if (props.inline || /^\s*\$[\s\S]*\$\s*$/.test(value)) {
    value = value.replace(/\s*\r?\n\s*/g, ' ')
  }

  const lines = value.split(/\r?\n/).filter((line) => line.trim() || value.includes('\n'))
  return (lines.length ? lines : ['']).map((line, index) => {
    if (isDisplayFormulaLine(line)) {
      const formula = cleanupFormula(line.replace(/^\s*\$\$|\$\$\s*$/g, ''))
      return {
        key: `display-${index}`,
        type: 'display',
        html: renderMath(formula, false)
      }
    }

    const trimmed = cleanupFormula(line)
    if (!props.inline && trimmed && isComplexLatex(toLatex(trimmed)) && isMathCandidate(trimmed) && !/[，。；：、\u4e00-\u9fa5]/.test(trimmed)) {
      return {
        key: `display-auto-${index}`,
        type: 'display',
        html: renderMath(trimmed, false)
      }
    }

    return {
      key: `line-${index}`,
      type: 'line',
      parts: parseInlineMath(line)
    }
  })
})

function fitDisplayMath() {
  const root = containerRef.value
  if (!root) return

  root.querySelectorAll('.math-display').forEach((display) => {
    const inner = display.querySelector('.math-display-fit')
    if (!inner) return

    inner.style.transform = ''
    display.style.height = ''
    const available = Math.max(display.clientWidth || root.clientWidth || 0, 1)
    const naturalWidth = Math.max(inner.scrollWidth, inner.getBoundingClientRect().width)
    const naturalHeight = Math.max(inner.scrollHeight, inner.getBoundingClientRect().height)
    const scale = naturalWidth > available ? Math.max(available / naturalWidth, 0.38) : 1

    inner.style.setProperty('--math-scale', String(scale))
    inner.style.transform = `scale(${scale})`
    display.style.height = `${Math.ceil(naturalHeight * scale) + 4}px`
  })
}

async function scheduleFit() {
  await nextTick()
  fitDisplayMath()
}

watch(renderedLines, scheduleFit, { flush: 'post' })

onMounted(() => {
  scheduleFit()
  if (typeof ResizeObserver !== 'undefined' && containerRef.value) {
    resizeObserver = new ResizeObserver(() => fitDisplayMath())
    resizeObserver.observe(containerRef.value)
  }
  window.addEventListener('resize', fitDisplayMath)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  window.removeEventListener('resize', fitDisplayMath)
})
</script>

<style scoped>
.math-text {
  min-width: 0;
  max-width: 100%;
  overflow: visible;
  overflow-y: visible;
  color: inherit;
  line-height: 1.85;
}

.math-line {
  margin: 0;
  overflow-wrap: normal;
  word-break: normal;
}

.math-line + .math-line,
.math-display + .math-line,
.math-line + .math-display,
.math-display + .math-display {
  margin-top: 6px;
}

.math-inline {
  display: inline-block;
  max-width: none;
  overflow: visible;
  white-space: nowrap;
  vertical-align: -0.08em;
  line-height: 1;
}

.math-display {
  position: relative;
  display: block;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
  padding: 2px 0;
  white-space: nowrap;
}

.math-display-fit {
  display: inline-block;
  min-width: max-content;
  max-width: none;
  transform-origin: left top;
  white-space: nowrap;
}

.math-inline :deep(.katex),
.math-display :deep(.katex) {
  white-space: nowrap;
}

.math-inline :deep(.katex-html),
.math-display :deep(.katex-html) {
  white-space: nowrap;
}

.math-display :deep(.katex-display) {
  display: inline-block;
  min-width: max-content;
  margin: 0;
}

.compact {
  line-height: 1.58;
}

.compact .math-line + .math-line {
  margin-top: 2px;
}

.block {
  width: 100%;
}

.inlineMode {
  display: inline;
  overflow: visible;
}

.inlineMode .math-line {
  display: inline;
}
</style>
