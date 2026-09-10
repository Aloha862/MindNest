export function statusText(status) {
  const map = {
    active: '已激活',
    disabled: '已禁用',
    uploaded: '已上传',
    processing: '处理中',
    recognized: '已识别',
    pending: '等待处理',
    preprocessing: '预处理中',
    yolo_running: 'YOLO 检测中',
    ocr_running: 'OCR 识别中',
    formula_running: '公式识别中',
    vlm_running: 'VLM 分析中',
    parsing: '结果校验中',
    persisting: '写入题卡中',
    completed: '已完成',
    needs_review: '待复核',
    failed: '失败',
    success: '成功'
  }
  return map[status] || status
}

export function difficultyType(difficulty) {
  return difficulty === '基础' ? 'success' : difficulty === '进阶' ? 'warning' : 'danger'
}

export function formatFileSize(size) {
  const value = Number(size || 0)
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(2)} MB`
}

export function safeDate(value, fallback = '—') {
  return value ? String(value).slice(0, 19) : fallback
}

export function costText(value) {
  if (value === null || value === undefined || value === '') return '—'
  return `${value} ms`
}
