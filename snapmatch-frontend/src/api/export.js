import request from './request'

const extensionMap = {
  markdown: 'md',
  word: 'docx',
  pdf: 'pdf'
}

export async function exportQuestions(payload) {
  const format = (payload.format || 'markdown').toLowerCase()
  const blob = await request.post('/export', payload, { responseType: 'blob' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `snapmatch-export.${extensionMap[format] || format}`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
