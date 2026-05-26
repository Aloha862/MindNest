import request from './request'

export const startRecognition = (payload) => {
  const body = typeof payload === 'object' ? payload : { fileId: payload }
  return request.post('/recognition/start', body)
}
export const batchStartRecognition = (payload) => request.post('/recognition/batch-start', payload)
export const getTasks = (params) => request.get('/recognition/tasks', { params })
export const getTaskDetail = (id) => request.get(`/recognition/tasks/${id}`)
export const getTaskProgress = (id) => request.get(`/recognition/tasks/${id}/progress`)
export const getTaskDiagnostics = (id) => request.get(`/recognition/tasks/${id}/diagnostics`)
export const getRecognitionBatch = (batchId) => request.get(`/recognition/batches/${batchId}`)
export const getOCRResult = (id) => request.get(`/recognition/${id}/ocr`)
export const getVLMResult = (id) => request.get(`/recognition/${id}/vlm`)
export const retryTask = (id) => request.post(`/recognition/tasks/${id}/retry`)
