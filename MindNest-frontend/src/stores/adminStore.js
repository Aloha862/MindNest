import { defineStore } from 'pinia'
import { getAdminDashboard } from '@/api/admin'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    dashboard: null
  }),
  actions: {
    async fetchDashboard() {
      const res = await getAdminDashboard()
      this.dashboard = res.data
      return res.data
    }
  }
})
