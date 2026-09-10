import { defineStore } from 'pinia'
import { getDashboard } from '@/api/user'

export const useUserStore = defineStore('user', {
  state: () => ({
    dashboard: null
  }),
  actions: {
    async fetchDashboard() {
      const res = await getDashboard()
      this.dashboard = res.data
      return res.data
    }
  }
})
