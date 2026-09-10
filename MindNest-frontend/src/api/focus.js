import request from './request'

export const startFocusSession = (payload = {}) => request.post('/focus/start', payload)
export const getCurrentFocusSession = () => request.get('/focus/current')
export const submitFocusState = (payload) => request.post('/focus/state', payload)
export const analyzeFocusFrame = (payload) => request.post('/focus/analyze-frame', payload, { timeout: 300000 })
export const endFocusSession = (sessionId) => request.post('/focus/end', { sessionId })
