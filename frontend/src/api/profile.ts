import apiClient from './client'
import type { Profile } from '@/types'

export const profileApi = {
  async get(): Promise<Profile | null> {
    const response = await apiClient.get('/api/profile')
    return response.data
  },

  async update(data: Partial<Profile>): Promise<Profile> {
    const response = await apiClient.put('/api/profile', data)
    return response.data
  },

  async regenerate(): Promise<Profile> {
    const response = await apiClient.post('/api/profile/regenerate')
    return response.data
  },
}
