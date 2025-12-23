<script setup lang="ts">
import { ref } from 'vue'
import { useVacanciesStore } from '@/stores/vacancies'
import { resumesApi } from '@/api/resumes'

const vacanciesStore = useVacanciesStore()

const searchText = ref('')
const area = ref('')
const analyzing = ref<number | null>(null)
const creating = ref<number | null>(null)

async function handleSearch() {
  await vacanciesStore.search({
    text: searchText.value || undefined,
    area: area.value || undefined,
    per_page: 20,
  })
}

async function handleAnalyze(id: number) {
  analyzing.value = id
  try {
    const result = await vacanciesStore.analyzeVacancy(id)
    alert(`Match Score: ${result.match_score}%\n\nПодходящие навыки: ${result.matching_skills.join(', ')}\n\nНе хватает: ${result.missing_skills.join(', ')}`)
  } catch {
    alert('Ошибка анализа. Убедитесь что профиль создан.')
  } finally {
    analyzing.value = null
  }
}

async function handleCreateResume(vacancyId: number) {
  creating.value = vacancyId
  try {
    await resumesApi.createVariation(vacancyId)
    alert('Резюме создано! Перейдите в раздел "Резюме".')
  } catch {
    alert('Ошибка создания резюме. Убедитесь что базовое резюме создано.')
  } finally {
    creating.value = null
  }
}

function formatSalary(from: number | null, to: number | null, currency: string | null) {
  if (!from && !to) return 'Не указана'
  const parts = []
  if (from) parts.push(`от ${from.toLocaleString()}`)
  if (to) parts.push(`до ${to.toLocaleString()}`)
  return parts.join(' ') + (currency ? ` ${currency}` : '')
}
</script>

<template>
  <div class="vacancies-view">
    <div class="page-header">
      <h1>Вакансии</h1>
    </div>

    <!-- Search Form -->
    <div class="search-form card">
      <div class="search-inputs">
        <input
          v-model="searchText"
          placeholder="Python Backend Москва..."
          @keydown.enter="handleSearch"
        />
        <select v-model="area">
          <option value="">Все регионы</option>
          <option value="1">Москва</option>
          <option value="2">Санкт-Петербург</option>
          <option value="113">Россия</option>
        </select>
        <button class="primary" @click="handleSearch" :disabled="vacanciesStore.loading">
          {{ vacanciesStore.loading ? 'Поиск...' : 'Искать' }}
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="vacanciesStore.vacancies.length" class="results-info">
      Найдено: {{ vacanciesStore.total.toLocaleString() }} вакансий
    </div>

    <div class="vacancies-list">
      <div
        v-for="vacancy in vacanciesStore.vacancies"
        :key="vacancy.id"
        class="vacancy-card card"
      >
        <div class="vacancy-header">
          <div class="vacancy-match" v-if="vacancy.match_score !== null">
            <span class="match-score" :class="{
              high: vacancy.match_score >= 80,
              medium: vacancy.match_score >= 50 && vacancy.match_score < 80,
              low: vacancy.match_score < 50
            }">
              {{ Math.round(vacancy.match_score) }}%
            </span>
          </div>
          <div class="vacancy-info">
            <h3 class="vacancy-title">{{ vacancy.title }}</h3>
            <p class="vacancy-company">{{ vacancy.company_name }}</p>
          </div>
        </div>

        <div class="vacancy-meta">
          <span>{{ formatSalary(vacancy.salary_from, vacancy.salary_to, vacancy.salary_currency) }}</span>
          <span>{{ vacancy.location }}</span>
          <span v-if="vacancy.experience">{{ vacancy.experience }}</span>
        </div>

        <p v-if="vacancy.requirements" class="vacancy-requirements">
          {{ vacancy.requirements }}
        </p>

        <div class="vacancy-actions">
          <button
            class="secondary"
            @click="handleAnalyze(vacancy.id)"
            :disabled="analyzing === vacancy.id"
          >
            {{ analyzing === vacancy.id ? 'Анализ...' : 'Анализировать' }}
          </button>
          <button
            class="primary"
            @click="handleCreateResume(vacancy.id)"
            :disabled="creating === vacancy.id"
          >
            {{ creating === vacancy.id ? 'Создание...' : 'Создать резюме' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="!vacanciesStore.loading && !vacanciesStore.vacancies.length" class="empty-state">
      <p>Введите поисковый запрос чтобы найти вакансии</p>
    </div>
  </div>
</template>

<style scoped>
.vacancies-view {
  max-width: 900px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.search-form {
  margin-bottom: 24px;
}

.search-inputs {
  display: flex;
  gap: 12px;
}

.search-inputs input {
  flex: 1;
}

.search-inputs select {
  width: 180px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
}

.results-info {
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.vacancies-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vacancy-card {
  padding: 20px;
}

.vacancy-header {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.vacancy-match {
  flex-shrink: 0;
}

.match-score {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 600;
}

.match-score.high {
  background: #D1FAE5;
  color: #059669;
}

.match-score.medium {
  background: #FEF3C7;
  color: #D97706;
}

.match-score.low {
  background: #FEE2E2;
  color: #DC2626;
}

.vacancy-info {
  flex: 1;
}

.vacancy-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
}

.vacancy-company {
  color: var(--text-secondary);
  font-size: 14px;
}

.vacancy-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 14px;
  color: var(--text-secondary);
}

.vacancy-requirements {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.vacancy-actions {
  display: flex;
  gap: 12px;
}

.vacancy-actions button {
  padding: 8px 16px;
  font-size: 13px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}
</style>
