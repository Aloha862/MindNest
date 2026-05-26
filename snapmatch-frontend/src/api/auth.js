import request from './request'

export const login = (payload) => request.post('/auth/login', payload)
export const register = (payload) => request.post('/auth/register', payload)
export const logout = () => request.post('/auth/logout')
export const getMe = () => request.get('/auth/me')
export const changePassword = (payload) => request.put('/auth/password', payload)
