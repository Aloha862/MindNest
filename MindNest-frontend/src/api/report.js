import request from './request'

export const getDailyReport = () => request.get('/report/daily')
export const getStudySessions = (params = {}) => request.get('/report/sessions', { params })
export const getStudySessionReport = (id) => request.get(`/report/sessions/${id}`)
