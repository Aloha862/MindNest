import request from './request'

function normalizeDashboard(data = {}) {
  return {
    ...data,
    subjectStats: data.subjectStats || data.subjectDistribution || [],
    typeStats: data.typeStats || data.questionTypeDistribution || []
  }
}

export const getProfile = () => request.get('/user/profile')
export const updateProfile = (payload) => request.put('/user/profile', payload)
export const getDashboard = async () => {
  const res = await request.get('/user/dashboard')
  return { ...res, data: normalizeDashboard(res.data) }
}
