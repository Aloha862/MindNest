import request from './request'

function normalizeDashboard(data = {}) {
  const failed = (data.taskStatusDistribution || []).find((item) => item.name === 'failed')?.value || 0
  return {
    ...data,
    modelCallCount: data.modelCallCount || data.recentLogs?.length || 0,
    failedTaskCount: data.failedTaskCount || failed,
    uploadTrend: data.uploadTrend || [],
    failureReasons: data.failureReasons || [],
    modelLatency: data.modelLatency || [],
    ocrEmptyCount: data.ocrEmptyCount || 0,
    vlmInvalidJsonCount: data.vlmInvalidJsonCount || 0,
    lowQualityRate: data.lowQualityRate || 0,
    reviewRate: data.reviewRate || 0,
    batchSuccessRate: data.batchSuccessRate || 0
  }
}

export const getAdminDashboard = async () => {
  const res = await request.get('/admin/dashboard')
  return { ...res, data: normalizeDashboard(res.data) }
}
export const getAdminUsers = (params) => request.get('/admin/users', { params })
export const updateUserStatus = (id, status) => request.put(`/admin/users/${id}/status`, { status })
export const deleteAdminUser = (id) => request.delete(`/admin/users/${id}`)
export const getAdminFiles = (params) => request.get('/admin/files', { params })
export const deleteAdminFile = (id) => request.delete(`/admin/files/${id}`)
export const getAdminTasks = (params) => request.get('/admin/recognition-tasks', { params })
export const getAdminQuestions = (params) => request.get('/admin/questions', { params })
export const getModelLogs = (params) => request.get('/admin/model-logs', { params })
export const getAdminReviewTasks = () => request.get('/admin/review-tasks')
export const getAdminStatistics = () => request.get('/admin/statistics')
export const getSystemConfig = () => request.get('/admin/system-config')
export const updateSystemConfig = (payload) => request.put('/admin/system-config', payload)
