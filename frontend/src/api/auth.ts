import apiClient from './client'
import type { AuthStatus } from '@/types'

export const authApi = {
  async getStatus(): Promise<AuthStatus> {
    const response = await apiClient.get('/api/auth/status')
    return response.data
  },

  getHHLoginUrl(): string {
    return `${import.meta.env.VITE_API_URL || ''}/api/auth/hh/login`
  },

  async logout(): Promise<void> {
    await apiClient.post('/api/auth/logout')
  },
}
