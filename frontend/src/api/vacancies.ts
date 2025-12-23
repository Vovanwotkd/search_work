import apiClient from './client'
import type { VacancySearchResult, Vacancy } from '@/types'

export interface VacancySearchParams {
  text?: string
  area?: string
  salary?: number
  experience?: string
  employment?: string
  schedule?: string
  page?: number
  per_page?: number
}

export const vacanciesApi = {
  async search(params: VacancySearchParams): Promise<VacancySearchResult> {
    const response = await apiClient.get('/api/hh/vacancies', { params })
    return response.data
  },

  async getById(id: number): Promise<Vacancy> {
    const response = await apiClient.get(`/api/hh/vacancies/${id}`)
    return response.data
  },

  async analyze(id: number): Promise<{
    vacancy_id: number
    match_score: number
    matching_skills: string[]
    missing_skills: string[]
    recommendations: string[]
  }> {
    const response = await apiClient.post(`/api/hh/vacancies/${id}/analyze`)
    return response.data
  },
}

export interface HHResume {
  id: string
  title: string
  status: string
  created_at: string
  updated_at: string
  url: string
  total_views: number
}

export const hhApi = {
  async getMyResumes(): Promise<{ resumes: HHResume[] }> {
    const response = await apiClient.get('/api/hh/resumes/mine')
    return response.data
  },

  async importResume(resumeId: string): Promise<{
    message: string
    resume_id: number
    title: string
  }> {
    const response = await apiClient.post(`/api/hh/resumes/${resumeId}/import`)
    return response.data
  },
}
