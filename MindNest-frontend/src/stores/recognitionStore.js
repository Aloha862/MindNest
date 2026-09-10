import { defineStore } from 'pinia'
import { getTasks, startRecognition } from '@/api/recognition'

export const useRecognitionStore = defineStore('recognition', {
  state: () => ({
    tasks: []
  }),
  actions: {
    async fetchTasks(params) {
      const res = await getTasks(params)
      this.tasks = res.data.list
      return res.data
    },
    async createTask(fileId) {
      const res = await startRecognition(fileId)
      this.tasks.unshift(res.data)
      return res.data
    }
  }
})
