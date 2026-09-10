import request from './request'

function normalizeStatistics(data = {}) {
  return {
    ...data,
    subjectStats: data.subjectStats || data.subjectDistribution || [],
    typeStats: data.typeStats || data.questionTypeDistribution || [],
    difficultyStats: data.difficultyStats || data.difficultyDistribution || []
  }
}

export const getQuestions = (params) => request.get('/questions', { params })
export const getQuestionDetail = (id) => request.get(`/questions/${id}`)
export const createQuestion = (payload) => request.post('/questions', payload)
export const updateQuestion = (id, payload) => request.put(`/questions/${id}`, payload)
export const deleteQuestion = (id) => request.delete(`/questions/${id}`)
export const markQuestionWrong = (id, payload = {}) => request.post(`/questions/${id}/wrong`, payload)
export const unmarkQuestionWrong = (id) => request.delete(`/questions/${id}/wrong`)
export const getQuestionKnowledgeStats = () => request.get('/questions/knowledge-stats')
export const getQuestionStatistics = async () => {
  const res = await request.get('/questions/statistics')
  return { ...res, data: normalizeStatistics(res.data) }
}
export const getSubjects = () => request.get('/subjects')
export const getTags = () => request.get('/questions/tags')
