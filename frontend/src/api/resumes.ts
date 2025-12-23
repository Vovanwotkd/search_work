import apiClient from './client'
import type { BaseResume, ResumeVariation } from '@/types'

export const resumesApi = {
  // Base Resume
  async getBase(): Promise<BaseResume | null> {
    const response = await apiClient.get('/api/resumes/base')
    return response.data
  },

  async createBase(): Promise<BaseResume> {
    const response = await apiClient.post('/api/resumes/base')
    return response.data
  },

  async updateBase(data: { title: string; content?: Record<string, unknown> }): Promise<BaseResume> {
    const response = await apiClient.put('/api/resumes/base', data)
    return response.data
  },

  // Variations
  async listVariations(): Promise<ResumeVariation[]> {
    const response = await apiClient.get('/api/resumes/variations')
    return response.data
  },

  async createVariation(vacancyId: number): Promise<ResumeVariation> {
    const response = await apiClient.post('/api/resumes/variations', { vacancy_id: vacancyId })
    return response.data
  },

  async getVariation(id: number): Promise<ResumeVariation> {
    const response = await apiClient.get(`/api/resumes/variations/${id}`)
    return response.data
  },

  async deleteVariation(id: number): Promise<void> {
    await apiClient.delete(`/api/resumes/variations/${id}`)
  },

  async generateCoverLetter(id: number): Promise<{ cover_letter: string }> {
    const response = await apiClient.post(`/api/resumes/variations/${id}/cover-letter`)
    return response.data
  },

  async publish(id: number): Promise<{ message: string; hh_resume_id: string }> {
    const response = await apiClient.post(`/api/resumes/variations/${id}/publish`)
    return response.data
  },
}
