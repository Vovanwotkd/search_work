import apiClient from './client'
import type { Settings } from '@/types'

export const settingsApi = {
  async get(): Promise<Settings> {
    const response = await apiClient.get('/api/settings')
    return response.data
  },

  async update(data: {
    llm_provider?: 'claude' | 'openai'
    claude_api_key?: string
    openai_api_key?: string
  }): Promise<Settings> {
    const response = await apiClient.put('/api/settings', data)
    return response.data
  },
}
