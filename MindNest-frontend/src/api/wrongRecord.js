import request from './request'

export const getWrongRecords = (params) => request.get('/wrong-records', { params })
export const getWrongStatistics = () => request.get('/wrong-records/statistics')
export const getWrongKnowledgeStats = () => request.get('/wrong-records/knowledge-stats')
export const updateWrongRecord = (id, payload) => request.put(`/wrong-records/${id}`, payload)
export const createWrongAttempt = (id, payload) => request.post(`/wrong-records/${id}/attempts`, payload)
export const getWrongAttempts = (id) => request.get(`/wrong-records/${id}/attempts`)
export const masterWrongRecord = (id) => request.post(`/wrong-records/${id}/master`)
export const reopenWrongRecord = (id) => request.post(`/wrong-records/${id}/reopen`)
