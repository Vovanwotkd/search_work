import apiClient from './client'

export interface Specialization {
  id: string
  name: string
  count?: number
}

export interface City {
  id: string
  name: string
}

export interface AutomationConfig {
  specializations: string[]
  cities: string[]
  auto_apply: boolean
  max_resumes: number
}

export interface VacancyRecommendation {
  vacancy_id: string
  title: string
  company: string
  match_score: number
  reason: string
}

export interface AutomationStatus {
  status: 'idle' | 'running' | 'completed' | 'error'
  phase: 'loading' | 'analyzing' | 'generating' | 'applying' | null
  message: string
  vacancies_loaded: number
  vacancies_total: number
  vacancies_analyzed: number
  resumes_generated: number
  applications_sent: number
  recommendations: VacancyRecommendation[]
  error?: string
}

export interface GithubAnalysis {
  username: string
  skills: string[]
  languages: string[]
  repos_analyzed: number
}

export const automationApi = {
  async getSpecializations(): Promise<Specialization[]> {
    const response = await apiClient.get('/api/automation/specializations')
    return response.data
  },

  async getCities(): Promise<City[]> {
    const response = await apiClient.get('/api/automation/cities')
    return response.data
  },

  async analyzeGithub(username: string): Promise<GithubAnalysis> {
    const response = await apiClient.post('/api/automation/analyze-github', { username })
    return response.data
  },

  async start(config: AutomationConfig): Promise<{ message: string }> {
    const response = await apiClient.post('/api/automation/start', config)
    return response.data
  },

  async stop(): Promise<{ message: string }> {
    const response = await apiClient.post('/api/automation/stop')
    return response.data
  },

  async getStatus(): Promise<AutomationStatus> {
    const response = await apiClient.get('/api/automation/status')
    return response.data
  },

  async getRecommendations(): Promise<VacancyRecommendation[]> {
    const response = await apiClient.get('/api/automation/recommendations')
    return response.data
  },
}
