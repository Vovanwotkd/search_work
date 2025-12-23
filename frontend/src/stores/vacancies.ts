import { defineStore } from 'pinia'
import { ref } from 'vue'
import { vacanciesApi, type VacancySearchParams } from '@/api/vacancies'
import type { Vacancy } from '@/types'

export const useVacanciesStore = defineStore('vacancies', () => {
  const vacancies = ref<Vacancy[]>([])
  const total = ref(0)
  const page = ref(0)
  const pages = ref(0)
  const loading = ref(false)
  const searchParams = ref<VacancySearchParams>({})

  async function search(params: VacancySearchParams) {
    loading.value = true
    searchParams.value = params
    try {
      const result = await vacanciesApi.search(params)
      vacancies.value = result.items
      total.value = result.found
      page.value = result.page
      pages.value = result.pages
    } catch (error) {
      console.error('Failed to search vacancies:', error)
    } finally {
      loading.value = false
    }
  }

  async function analyzeVacancy(id: number) {
    try {
      const result = await vacanciesApi.analyze(id)
      // Update vacancy in list with match score
      const index = vacancies.value.findIndex(v => v.id === id)
      if (index !== -1) {
        vacancies.value[index].match_score = result.match_score
      }
      return result
    } catch (error) {
      console.error('Failed to analyze vacancy:', error)
      throw error
    }
  }

  return {
    vacancies,
    total,
    page,
    pages,
    loading,
    searchParams,
    search,
    analyzeVacancy,
  }
})
