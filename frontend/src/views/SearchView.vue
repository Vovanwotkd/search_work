<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { searchApi, type SearchParams, type Vacancy, type Area, type ProfessionalCategory, type Industry } from '../api/search'

// State
const loading = ref(false)
const exporting = ref(false)

// Dictionaries
const dictionaries = ref<any>(null)
const russiaAreas = ref<Area | null>(null)
const professionalRoles = ref<ProfessionalCategory[]>([])
const industries = ref<Industry[]>([])

// Search params
const searchText = ref('')
const selectedAreas = ref<string[]>([])
const selectedRoles = ref<string[]>([])
const selectedIndustries = ref<string[]>([])
const selectedExperience = ref('')
const selectedEmployment = ref<string[]>([])
const selectedSchedule = ref<string[]>([])
const minSalary = ref<number | null>(null)
const onlyWithSalary = ref(false)
const orderBy = ref('relevance')
const period = ref<number | null>(null)

// Results
const vacancies = ref<Vacancy[]>([])
const totalFound = ref(0)
const currentPage = ref(0)
const totalPages = ref(0)

// Dialogs
const showAreaDialog = ref(false)
const showRolesDialog = ref(false)
const areaSearch = ref('')
const roleSearch = ref('')

// Load dictionaries
onMounted(async () => {
  try {
    const [dicts, areas, roles, inds] = await Promise.all([
      searchApi.getDictionaries(),
      searchApi.getRussiaAreas(),
      searchApi.getProfessionalRoles(),
      searchApi.getIndustries(),
    ])
    dictionaries.value = dicts
    russiaAreas.value = areas
    professionalRoles.value = roles.categories || []
    industries.value = inds
  } catch (e) {
    console.error('Failed to load dictionaries:', e)
  }
})

// Filtered areas (for search)
const filteredAreas = computed(() => {
  if (!russiaAreas.value?.areas) return []
  const search = areaSearch.value.toLowerCase()
  if (!search) return russiaAreas.value.areas

  const result: Area[] = []
  const searchInAreas = (areas: Area[]) => {
    for (const area of areas) {
      if (area.name.toLowerCase().includes(search)) {
        result.push(area)
      }
      if (area.areas?.length) {
        searchInAreas(area.areas)
      }
    }
  }
  searchInAreas(russiaAreas.value.areas)
  return result.slice(0, 50) // Limit results
})

// Filtered roles
const filteredRoles = computed(() => {
  const search = roleSearch.value.toLowerCase()
  if (!search) return professionalRoles.value

  return professionalRoles.value.map(cat => ({
    ...cat,
    roles: cat.roles.filter(r => r.name.toLowerCase().includes(search))
  })).filter(cat => cat.roles.length > 0)
})

// Selected names for display
const selectedAreaNames = computed(() => {
  const names: string[] = []
  const findArea = (areas: Area[], id: string): string | null => {
    for (const area of areas) {
      if (area.id === id) return area.name
      if (area.areas?.length) {
        const found = findArea(area.areas, id)
        if (found) return found
      }
    }
    return null
  }
  if (russiaAreas.value?.areas) {
    for (const id of selectedAreas.value) {
      const name = findArea(russiaAreas.value.areas, id)
      if (name) names.push(name)
    }
  }
  return names
})

const selectedRoleNames = computed(() => {
  const names: string[] = []
  for (const id of selectedRoles.value) {
    for (const cat of professionalRoles.value) {
      const role = cat.roles.find(r => r.id === id)
      if (role) names.push(role.name)
    }
  }
  return names
})

// Build search params
const buildSearchParams = (): SearchParams => ({
  text: searchText.value || undefined,
  area: selectedAreas.value.length ? selectedAreas.value : undefined,
  salary: minSalary.value || undefined,
  only_with_salary: onlyWithSalary.value || undefined,
  experience: selectedExperience.value || undefined,
  employment: selectedEmployment.value.length ? selectedEmployment.value : undefined,
  schedule: selectedSchedule.value.length ? selectedSchedule.value : undefined,
  professional_role: selectedRoles.value.length ? selectedRoles.value : undefined,
  industry: selectedIndustries.value.length ? selectedIndustries.value : undefined,
  period: period.value || undefined,
  order_by: orderBy.value,
})

// Search
const search = async (page = 0) => {
  loading.value = true
  try {
    const result = await searchApi.searchVacancies(buildSearchParams(), page, 20)
    vacancies.value = result.items
    totalFound.value = result.found
    currentPage.value = result.page
    totalPages.value = result.pages
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    loading.value = false
  }
}

// Export
const exportVacancies = async (format: 'json' | 'csv') => {
  exporting.value = true
  try {
    if (format === 'csv') {
      const blob = await searchApi.exportVacancies(buildSearchParams(), 'csv', 20) as Blob
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'vacancies.csv'
      a.click()
      URL.revokeObjectURL(url)
    } else {
      const result = await searchApi.exportVacancies(buildSearchParams(), 'json', 20) as any
      const blob = new Blob([JSON.stringify(result.items, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'vacancies.json'
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (e) {
    console.error('Export failed:', e)
  } finally {
    exporting.value = false
  }
}

// Format salary
const formatSalary = (vacancy: Vacancy): string => {
  if (!vacancy.salary) return 'Не указана'
  const { from, to, currency } = vacancy.salary
  if (from && to) return `${from.toLocaleString()} - ${to.toLocaleString()} ${currency}`
  if (from) return `от ${from.toLocaleString()} ${currency}`
  if (to) return `до ${to.toLocaleString()} ${currency}`
  return 'Не указана'
}

// Toggle selection
const toggleArea = (id: string) => {
  const idx = selectedAreas.value.indexOf(id)
  if (idx >= 0) selectedAreas.value.splice(idx, 1)
  else selectedAreas.value.push(id)
}

const toggleRole = (id: string) => {
  const idx = selectedRoles.value.indexOf(id)
  if (idx >= 0) selectedRoles.value.splice(idx, 1)
  else selectedRoles.value.push(id)
}
</script>

<template>
  <div class="search-view">
    <h1>Поиск вакансий</h1>
    <p class="subtitle">Поиск с фильтрами и экспортом</p>

    <!-- Filters -->
    <div class="filters">
      <!-- Text search -->
      <div class="filter-group">
        <label>Ключевые слова</label>
        <input v-model="searchText" type="text" placeholder="Профессия или должность" />
      </div>

      <!-- Areas -->
      <div class="filter-group">
        <label>Регион</label>
        <div class="chips-container">
          <span v-for="name in selectedAreaNames" :key="name" class="chip">{{ name }}</span>
          <button class="chip-add" @click="showAreaDialog = true">+ Добавить</button>
        </div>
      </div>

      <!-- Professional roles -->
      <div class="filter-group">
        <label>Специализация</label>
        <div class="chips-container">
          <span v-for="name in selectedRoleNames" :key="name" class="chip">{{ name }}</span>
          <button class="chip-add" @click="showRolesDialog = true">+ Добавить</button>
        </div>
      </div>

      <!-- Salary -->
      <div class="filter-group">
        <label>Зарплата</label>
        <div class="salary-row">
          <input v-model.number="minSalary" type="number" placeholder="от" />
          <label class="checkbox-label">
            <input v-model="onlyWithSalary" type="checkbox" />
            Только с указанной зарплатой
          </label>
        </div>
      </div>

      <!-- Experience -->
      <div class="filter-group" v-if="dictionaries">
        <label>Опыт работы</label>
        <select v-model="selectedExperience">
          <option value="">Любой</option>
          <option v-for="exp in dictionaries.experience" :key="exp.id" :value="exp.id">
            {{ exp.name }}
          </option>
        </select>
      </div>

      <!-- Employment type -->
      <div class="filter-group" v-if="dictionaries">
        <label>Тип занятости</label>
        <div class="checkbox-list">
          <label v-for="emp in dictionaries.employment" :key="emp.id" class="checkbox-label">
            <input type="checkbox" :value="emp.id" v-model="selectedEmployment" />
            {{ emp.name }}
          </label>
        </div>
      </div>

      <!-- Schedule -->
      <div class="filter-group" v-if="dictionaries">
        <label>График работы</label>
        <div class="checkbox-list">
          <label v-for="sch in dictionaries.schedule" :key="sch.id" class="checkbox-label">
            <input type="checkbox" :value="sch.id" v-model="selectedSchedule" />
            {{ sch.name }}
          </label>
        </div>
      </div>

      <!-- Order -->
      <div class="filter-group">
        <label>Сортировка</label>
        <select v-model="orderBy">
          <option value="relevance">По соответствию</option>
          <option value="publication_time">По дате</option>
          <option value="salary_desc">По убыванию зарплаты</option>
          <option value="salary_asc">По возрастанию зарплаты</option>
        </select>
      </div>

      <!-- Period -->
      <div class="filter-group">
        <label>Период публикации</label>
        <select v-model="period">
          <option :value="null">За всё время</option>
          <option :value="1">За сутки</option>
          <option :value="3">За 3 дня</option>
          <option :value="7">За неделю</option>
          <option :value="30">За месяц</option>
        </select>
      </div>
    </div>

    <!-- Actions -->
    <div class="actions">
      <button class="btn-primary" @click="search()" :disabled="loading">
        {{ loading ? 'Поиск...' : 'Найти' }}
      </button>
      <button class="btn-export" @click="exportVacancies('csv')" :disabled="exporting || !vacancies.length">
        {{ exporting ? 'Экспорт...' : 'Экспорт CSV' }}
      </button>
      <button class="btn-export" @click="exportVacancies('json')" :disabled="exporting || !vacancies.length">
        Экспорт JSON
      </button>
    </div>

    <!-- Results info -->
    <div class="results-info" v-if="totalFound > 0">
      <span>Найдено: <strong>{{ totalFound.toLocaleString() }}</strong> вакансий</span>
      <span v-if="totalPages > 1">Страница {{ currentPage + 1 }} из {{ totalPages }}</span>
    </div>

    <!-- Results -->
    <div class="results">
      <div v-if="loading" class="loading">Загрузка...</div>

      <div v-else-if="vacancies.length === 0 && totalFound === 0" class="empty">
        Начните поиск, задав параметры фильтрации
      </div>

      <div v-else class="vacancy-list">
        <div v-for="v in vacancies" :key="v.id" class="vacancy-card">
          <div class="vacancy-header">
            <a :href="v.alternate_url" target="_blank" class="vacancy-title">{{ v.name }}</a>
            <span class="vacancy-salary">{{ formatSalary(v) }}</span>
          </div>
          <div class="vacancy-company">{{ v.employer.name }}</div>
          <div class="vacancy-location">{{ v.area.name }}</div>
          <div class="vacancy-meta">
            <span>{{ v.experience?.name }}</span>
            <span>{{ v.employment?.name }}</span>
            <span>{{ v.schedule?.name }}</span>
          </div>
          <div class="vacancy-snippet" v-if="v.snippet?.requirement">
            <div v-html="v.snippet.requirement"></div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination" v-if="totalPages > 1">
        <button @click="search(currentPage - 1)" :disabled="currentPage === 0">← Назад</button>
        <span>{{ currentPage + 1 }} / {{ totalPages }}</span>
        <button @click="search(currentPage + 1)" :disabled="currentPage >= totalPages - 1">Далее →</button>
      </div>
    </div>

    <!-- Area Dialog -->
    <div v-if="showAreaDialog" class="dialog-overlay" @click.self="showAreaDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h3>Выберите регион</h3>
          <button class="close-btn" @click="showAreaDialog = false">×</button>
        </div>
        <input v-model="areaSearch" type="text" placeholder="Поиск..." class="dialog-search" />
        <div class="dialog-content">
          <label v-for="area in filteredAreas" :key="area.id" class="checkbox-label">
            <input type="checkbox" :checked="selectedAreas.includes(area.id)" @change="toggleArea(area.id)" />
            {{ area.name }}
          </label>
        </div>
        <div class="dialog-footer">
          <button class="btn-primary" @click="showAreaDialog = false">Применить</button>
        </div>
      </div>
    </div>

    <!-- Roles Dialog -->
    <div v-if="showRolesDialog" class="dialog-overlay" @click.self="showRolesDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <h3>Выберите специализацию</h3>
          <button class="close-btn" @click="showRolesDialog = false">×</button>
        </div>
        <input v-model="roleSearch" type="text" placeholder="Поиск..." class="dialog-search" />
        <div class="dialog-content">
          <div v-for="cat in filteredRoles" :key="cat.id" class="role-category">
            <div class="category-name">{{ cat.name }}</div>
            <label v-for="role in cat.roles" :key="role.id" class="checkbox-label">
              <input type="checkbox" :checked="selectedRoles.includes(role.id)" @change="toggleRole(role.id)" />
              {{ role.name }}
            </label>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="btn-primary" @click="showRolesDialog = false">Применить</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

h1 {
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  margin-bottom: 2rem;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-weight: 500;
  color: #333;
}

.filter-group input[type="text"],
.filter-group input[type="number"],
.filter-group select {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.chip {
  background: #e8f4fc;
  color: #0066cc;
  padding: 0.5rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
}

.chip-add {
  background: none;
  border: 1px dashed #0066cc;
  color: #0066cc;
  padding: 0.5rem 0.75rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.875rem;
}

.chip-add:hover {
  background: #f0f7ff;
}

.salary-row {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.salary-row input {
  width: 120px;
}

.checkbox-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.btn-primary {
  background: #6c5ce7;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
}

.btn-primary:hover {
  background: #5b4bd6;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-export {
  background: #00b894;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
}

.btn-export:hover {
  background: #00a386;
}

.btn-export:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.results-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  color: #666;
}

.loading, .empty {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.vacancy-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.vacancy-card {
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 1.25rem;
}

.vacancy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.vacancy-title {
  font-size: 1.125rem;
  font-weight: 500;
  color: #0066cc;
  text-decoration: none;
}

.vacancy-title:hover {
  text-decoration: underline;
}

.vacancy-salary {
  font-weight: 600;
  color: #00b894;
  white-space: nowrap;
}

.vacancy-company {
  color: #333;
  margin-bottom: 0.25rem;
}

.vacancy-location {
  color: #666;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.vacancy-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.vacancy-snippet {
  font-size: 0.875rem;
  color: #666;
  line-height: 1.5;
}

.vacancy-snippet :deep(highlighttext) {
  background: #fff3cd;
  padding: 0 2px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
}

.pagination button {
  background: #f5f5f5;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button:hover:not(:disabled) {
  background: #e0e0e0;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Dialog */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
}

.dialog-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
}

.dialog-search {
  margin: 1rem 1.5rem;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dialog-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #eee;
  text-align: right;
}

.role-category {
  margin-bottom: 1rem;
}

.category-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
  padding-bottom: 0.25rem;
  border-bottom: 1px solid #eee;
}
</style>
