import apiClient from './client'
import type { ChatSession } from '@/types'

export const chatApi = {
  async getSession(): Promise<ChatSession> {
    const response = await apiClient.get('/api/chat/session')
    return response.data
  },

  async sendMessage(content: string): Promise<ChatSession> {
    const response = await apiClient.post('/api/chat/message', { content })
    return response.data
  },

  async complete(): Promise<{ session_id: number; profile_created: boolean; message: string }> {
    const response = await apiClient.post('/api/chat/complete')
    return response.data
  },

  async reset(): Promise<ChatSession> {
    const response = await apiClient.post('/api/chat/reset')
    return response.data
  },
}
