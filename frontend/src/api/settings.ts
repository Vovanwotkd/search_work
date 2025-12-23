import apiClient from './client'
import type { Settings } from '@/types'

export interface Prompts {
  interview_system: string
  interview_first_message: string
  prompt_injection: string
  prompt_injection_enabled: boolean
}

export const settingsApi = {
  async get(): Promise<Settings> {
    const response = await apiClient.get('/api/settings')
    return response.data
  },

  async update(data: {
    llm_provider?: 'claude' | 'openai'
    llm_model?: string
    claude_api_key?: string
    openai_api_key?: string
  }): Promise<Settings> {
    const response = await apiClient.put('/api/settings', data)
    return response.data
  },

  async getPrompts(): Promise<Prompts> {
    const response = await apiClient.get('/api/settings/prompts')
    return response.data
  },

  async updatePrompts(data: Partial<Prompts>): Promise<Prompts> {
    const response = await apiClient.put('/api/settings/prompts', data)
    return response.data
  },

  async resetPrompts(): Promise<void> {
    await apiClient.post('/api/settings/prompts/reset')
  },
}
