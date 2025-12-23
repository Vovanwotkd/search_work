import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'
import type { AuthStatus } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const status = ref<AuthStatus | null>(null)
  const loading = ref(false)

  async function checkAuth() {
    loading.value = true
    try {
      status.value = await authApi.getStatus()
    } catch (error) {
      console.error('Failed to check auth:', error)
    } finally {
      loading.value = false
    }
  }

  function loginHH() {
    window.location.href = authApi.getHHLoginUrl()
  }

  async function logout() {
    await authApi.logout()
    await checkAuth()
  }

  return {
    status,
    loading,
    checkAuth,
    loginHH,
    logout,
  }
})
