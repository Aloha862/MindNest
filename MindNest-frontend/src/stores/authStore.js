import { defineStore } from 'pinia'
import { login as loginApi, logout as logoutApi } from '@/api/auth'
import { clearAuth, getStoredUser, getToken, setStoredUser, setToken } from '@/utils/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: getToken(),
    userInfo: getStoredUser()
  }),
  getters: {
    isLogin: (state) => Boolean(state.token && state.userInfo),
    role: (state) => state.userInfo?.role
  },
  actions: {
    async login(payload) {
      const res = await loginApi(payload)
      this.token = res.data.token
      this.userInfo = res.data.userInfo
      setToken(this.token)
      setStoredUser(this.userInfo)
      return this.userInfo
    },
    async logout() {
      try {
        await logoutApi()
      } finally {
        this.token = ''
        this.userInfo = null
        clearAuth()
      }
    }
  }
})
