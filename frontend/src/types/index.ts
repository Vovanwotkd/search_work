export interface ChatMessage {
  role: 'assistant' | 'user'
  content: string
  timestamp?: string
}

export interface ChatSession {
  id: number
  messages: ChatMessage[]
  status: 'in_progress' | 'completed'
  created_at: string
  updated_at: string
}

export interface Profile {
  id: number
  skills: string[]
  experience_years: number | null
  preferred_position: string | null
  preferred_salary_min: number | null
  preferred_salary_max: number | null
  preferred_locations: string[]
  summary: string | null
  structured_profile: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface Vacancy {
  id: number
  hh_vacancy_id: string
  title: string | null
  company_name: string | null
  salary_from: number | null
  salary_to: number | null
  salary_currency: string | null
  location: string | null
  experience: string | null
  employment_type: string | null
  requirements: string | null
  description: string | null
  key_skills: string[]
  match_score: number | null
  fetched_at: string
}

export interface VacancySearchResult {
  items: Vacancy[]
  found: number
  page: number
  pages: number
  per_page: number
}

export interface BaseResume {
  id: number
  title: string | null
  content: Record<string, unknown> | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ResumeVariation {
  id: number
  base_resume_id: number
  vacancy_id: number | null
  hh_resume_id: string | null
  title: string | null
  content: Record<string, unknown> | null
  adaptations: Record<string, unknown> | null
  cover_letter: string | null
  status: 'draft' | 'published' | 'archived'
  created_at: string
  updated_at: string
}

export interface Settings {
  llm_provider: 'claude' | 'openai'
  hh_connected: boolean
  has_claude_key: boolean
  has_openai_key: boolean
}

export interface AuthStatus {
  is_authenticated: boolean
  hh_connected: boolean
  hh_user_id: string | null
}
