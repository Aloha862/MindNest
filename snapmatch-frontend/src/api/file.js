import request from './request'

function toFormData(payload) {
  const data = new FormData()
  data.append('file', payload.file)
  data.append('fileType', payload.fileType || 'homework')
  data.append('subjectHint', payload.subjectHint || '')
  data.append('remark', payload.remark || '')
  return data
}

function toBatchFormData(payload) {
  const data = new FormData()
  ;(payload.files || []).forEach((file) => data.append('files', file))
  data.append('fileType', payload.fileType || 'homework')
  data.append('subjectHint', payload.subjectHint || '')
  data.append('remark', payload.remark || '')
  return data
}

export const uploadFile = (payload) => request.post('/files/upload', toFormData(payload), {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const uploadBatchFiles = (payload) => request.post('/files/batch-upload', toBatchFormData(payload), {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const getUploadPolicy = () => request.get('/files/upload-policy')
export const getMyFiles = (params) => request.get('/files/mine', { params })
export const getFileDetail = (id) => request.get(`/files/${id}`)
export const deleteFile = (id) => request.delete(`/files/${id}`)
