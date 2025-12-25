import apiClient from './client'

export interface Area {
  id: string
  name: string
  parent_id: string | null
  areas: Area[]
}

export interface ProfessionalRole {
  id: string
  name: string
  accept_incomplete_resumes: boolean
  is_default: boolean
}

export interface ProfessionalCategory {
  id: string
  name: string
  roles: ProfessionalRole[]
}

export interface Industry {
  id: string
  name: string
  industries?: Industry[]
}

export interface Dictionaries {
  experience: { id: string; name: string }[]
  employment: { id: string; name: string }[]
  schedule: { id: string; name: string }[]
  vacancy_search_order: { id: string; name: string }[]
  vacancy_search_fields: { id: string; name: string }[]
}

export interface SearchParams {
  text?: string
  area?: string[]
  salary?: number
  only_with_salary?: boolean
  experience?: string
  employment?: string[]
  schedule?: string[]
  professional_role?: string[]
  industry?: string[]
  search_field?: string[]
  period?: number
  order_by?: string
}

export interface Vacancy {
  id: string
  name: string
  area: { id: string; name: string }
  salary: { from: number | null; to: number | null; currency: string; gross: boolean } | null
  employer: { id: string; name: string; logo_urls?: { original: string } }
  published_at: string
  alternate_url: string
  experience: { id: string; name: string }
  employment: { id: string; name: string }
  schedule: { id: string; name: string }
  snippet?: { requirement: string; responsibility: string }
}

export interface SearchResult {
  items: Vacancy[]
  found: number
  pages: number
  page: number
  per_page: number
}

export interface ExportResult {
  total: number
  items: Vacancy[]
}

export const searchApi = {
  async getDictionaries(): Promise<Dictionaries> {
    const response = await apiClient.get('/api/search/dictionaries')
    return response.data
  },

  async getAreas(): Promise<Area[]> {
    const response = await apiClient.get('/api/search/areas')
    return response.data
  },

  async getRussiaAreas(): Promise<Area> {
    const response = await apiClient.get('/api/search/areas/russia')
    return response.data
  },

  async getProfessionalRoles(): Promise<{ categories: ProfessionalCategory[] }> {
    const response = await apiClient.get('/api/search/professional-roles')
    return response.data
  },

  async getIndustries(): Promise<Industry[]> {
    const response = await apiClient.get('/api/search/industries')
    return response.data
  },

  async searchVacancies(params: SearchParams, page = 0, perPage = 20): Promise<SearchResult> {
    const queryParams = new URLSearchParams()

    if (params.text) queryParams.append('text', params.text)
    if (params.salary) queryParams.append('salary', params.salary.toString())
    if (params.only_with_salary) queryParams.append('only_with_salary', 'true')
    if (params.experience) queryParams.append('experience', params.experience)
    if (params.order_by) queryParams.append('order_by', params.order_by)
    if (params.period) queryParams.append('period', params.period.toString())

    params.area?.forEach(a => queryParams.append('area', a))
    params.employment?.forEach(e => queryParams.append('employment', e))
    params.schedule?.forEach(s => queryParams.append('schedule', s))
    params.professional_role?.forEach(pr => queryParams.append('professional_role', pr))
    params.industry?.forEach(i => queryParams.append('industry', i))
    params.search_field?.forEach(sf => queryParams.append('search_field', sf))

    queryParams.append('page', page.toString())
    queryParams.append('per_page', perPage.toString())

    const response = await apiClient.get(`/api/search/vacancies?${queryParams.toString()}`)
    return response.data
  },

  async exportVacancies(params: SearchParams, format: 'json' | 'csv' = 'json', maxPages = 20): Promise<ExportResult | Blob> {
    const response = await apiClient.post(
      `/api/search/vacancies/export?format=${format}&max_pages=${maxPages}`,
      params,
      { responseType: format === 'csv' ? 'blob' : 'json' }
    )
    return response.data
  },

  async getVacancyDetails(vacancyId: string): Promise<Vacancy> {
    const response = await apiClient.get(`/api/search/vacancies/${vacancyId}`)
    return response.data
  },
}
