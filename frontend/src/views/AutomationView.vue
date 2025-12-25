<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { hhApi } from '@/api/vacancies'
import { settingsApi } from '@/api/settings'
import { automationApi, type Specialization, type AutomationConfig, type AutomationStatus } from '@/api/automation'

// Steps
const currentStep = ref(1)
const totalSteps = 5

// Step 1: Profile Setup
const profileReady = ref(false)
const importingResume = ref(false)
const hhResumes = ref<any[]>([])
const loadingResumes = ref(false)
const githubUsername = ref('')
const analyzingGithub = ref(false)
const githubSkills = ref<string[]>([])
const hasGithubToken = ref(false)
const githubAnalysisResult = ref<{
  repos_analyzed: number
  private_repos_analyzed: number
  has_token: boolean
} | null>(null)

// Step 2: Search Config
const cities = ref<{ id: string; name: string }[]>([])
const selectedCities = ref<string[]>([])
const specializations = ref<Specialization[]>([])
const selectedSpecs = ref<string[]>([])
const loadingSpecs = ref(false)

// Step 3: Vacancy Loading
const vacanciesLoaded = ref(0)
const vacanciesTotal = ref(0)

// Step 4: Analysis
const analyzedCount = ref(0)
const recommendations = ref<any[]>([])

// Step 5: Resume Generation & Apply
const generatedCount = ref(0)
const appliedCount = ref(0)

// Status
const automationStatus = ref<AutomationStatus | null>(null)
const statusPolling = ref<number | null>(null)

const stepTitles = [
  'Подготовка профиля',
  'Настройка поиска',
  'Загрузка вакансий',
  'Анализ и рекомендации',
  'Резюме и отклики'
]

onMounted(async () => {
  await loadInitialData()
})

async function loadInitialData() {
  // Check GitHub token status
  try {
    const tokenStatus = await settingsApi.getGitHubToken()
    hasGithubToken.value = tokenStatus.has_token
  } catch {
    // Ignore
  }

  try {
    // Load HH resumes
    loadingResumes.value = true
    const result = await hhApi.getMyResumes()
    hhResumes.value = result.resumes || []
  } catch {
    // Ignore - user might not be connected
  } finally {
    loadingResumes.value = false
  }

  // Load specializations
  loadingSpecs.value = true
  try {
    const specs = await automationApi.getSpecializations()
    specializations.value = specs
  } catch {
    console.error('Failed to load specializations')
  } finally {
    loadingSpecs.value = false
  }

  // Load cities
  try {
    const citiesData = await automationApi.getCities()
    cities.value = citiesData
  } catch {
    // Use defaults
    cities.value = [
      { id: '1', name: 'Москва' },
      { id: '2', name: 'Санкт-Петербург' },
      { id: '41', name: 'Калининград' },
    ]
  }

  // Check if automation is already running
  try {
    automationStatus.value = await automationApi.getStatus()
    if (automationStatus.value?.status === 'running') {
      startStatusPolling()
    }
  } catch {
    // No active automation
  }
}

async function importHHResume(resumeId: string) {
  importingResume.value = true
  try {
    await hhApi.importResume(resumeId)
    profileReady.value = true
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Ошибка импорта')
  } finally {
    importingResume.value = false
  }
}

async function analyzeGithub() {
  if (!githubUsername.value) return
  analyzingGithub.value = true
  try {
    const result = await automationApi.analyzeGithub(githubUsername.value)
    githubSkills.value = result.skills
    githubAnalysisResult.value = {
      repos_analyzed: result.repos_analyzed,
      private_repos_analyzed: result.private_repos_analyzed || 0,
      has_token: result.has_token || false
    }
    profileReady.value = true
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Ошибка анализа GitHub')
  } finally {
    analyzingGithub.value = false
  }
}

function toggleSpec(specId: string) {
  const idx = selectedSpecs.value.indexOf(specId)
  if (idx >= 0) {
    selectedSpecs.value.splice(idx, 1)
  } else {
    selectedSpecs.value.push(specId)
  }
}

function toggleCity(cityId: string) {
  const idx = selectedCities.value.indexOf(cityId)
  if (idx >= 0) {
    selectedCities.value.splice(idx, 1)
  } else {
    selectedCities.value.push(cityId)
  }
}

async function startAutomation() {
  if (selectedSpecs.value.length === 0) {
    alert('Выберите хотя бы одну специализацию')
    return
  }
  if (selectedCities.value.length === 0) {
    alert('Выберите хотя бы один город')
    return
  }

  currentStep.value = 3

  try {
    const config: AutomationConfig = {
      specializations: selectedSpecs.value,
      cities: selectedCities.value,
      auto_apply: true,
      max_resumes: 20
    }

    await automationApi.start(config)
    startStatusPolling()
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Ошибка запуска автоматизации')
  }
}

function startStatusPolling() {
  if (statusPolling.value) return

  statusPolling.value = window.setInterval(async () => {
    try {
      automationStatus.value = await automationApi.getStatus()

      // Update UI based on status
      if (automationStatus.value) {
        vacanciesLoaded.value = automationStatus.value.vacancies_loaded || 0
        vacanciesTotal.value = automationStatus.value.vacancies_total || 0
        analyzedCount.value = automationStatus.value.vacancies_analyzed || 0
        generatedCount.value = automationStatus.value.resumes_generated || 0
        appliedCount.value = automationStatus.value.applications_sent || 0
        recommendations.value = automationStatus.value.recommendations || []

        // Update step based on phase
        if (automationStatus.value.phase === 'loading') currentStep.value = 3
        else if (automationStatus.value.phase === 'analyzing') currentStep.value = 4
        else if (automationStatus.value.phase === 'generating') currentStep.value = 5
        else if (automationStatus.value.phase === 'applying') currentStep.value = 5

        if (automationStatus.value.status === 'completed' || automationStatus.value.status === 'error') {
          stopStatusPolling()
        }
      }
    } catch {
      stopStatusPolling()
    }
  }, 2000)
}

function stopStatusPolling() {
  if (statusPolling.value) {
    clearInterval(statusPolling.value)
    statusPolling.value = null
  }
}

async function stopAutomation() {
  try {
    await automationApi.stop()
    stopStatusPolling()
    automationStatus.value = null
  } catch {
    alert('Ошибка остановки')
  }
}

function nextStep() {
  if (currentStep.value < totalSteps) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}
</script>

<template>
  <div class="automation-view">
    <div class="page-header">
      <h1>Автоматизация поиска</h1>
      <p class="subtitle">Автоматический поиск, анализ и отклик на вакансии</p>
    </div>

    <!-- Progress Steps -->
    <div class="steps-progress">
      <div
        v-for="(title, idx) in stepTitles"
        :key="idx"
        class="step"
        :class="{ active: currentStep === idx + 1, completed: currentStep > idx + 1 }"
      >
        <div class="step-number">{{ idx + 1 }}</div>
        <div class="step-title">{{ title }}</div>
      </div>
    </div>

    <!-- Running Status Banner -->
    <div v-if="automationStatus?.status === 'running'" class="status-banner running">
      <div class="status-icon">⚙️</div>
      <div class="status-info">
        <strong>Автоматизация запущена</strong>
        <p>{{ automationStatus.phase }}: {{ automationStatus.message }}</p>
      </div>
      <button class="danger" @click="stopAutomation">Остановить</button>
    </div>

    <!-- Step 1: Profile Setup -->
    <div v-if="currentStep === 1" class="step-content">
      <h2>Шаг 1: Подготовка профиля</h2>

      <div class="card">
        <h3>Импорт резюме с HH.ru</h3>
        <div v-if="loadingResumes" class="loading">Загрузка резюме...</div>
        <div v-else-if="hhResumes.length === 0" class="empty">
          Нет доступных резюме. Подключите HH.ru в настройках.
        </div>
        <div v-else class="resume-list">
          <div v-for="resume in hhResumes" :key="resume.id" class="resume-item">
            <div class="resume-info">
              <strong>{{ resume.title }}</strong>
              <span class="status">{{ resume.status }}</span>
            </div>
            <button
              @click="importHHResume(resume.id)"
              :disabled="importingResume"
              class="small"
            >
              {{ importingResume ? 'Импорт...' : 'Импортировать' }}
            </button>
          </div>
        </div>
      </div>

      <div class="card">
        <h3>Анализ GitHub профиля</h3>
        <p class="hint">Добавим навыки из ваших репозиториев</p>

        <div v-if="hasGithubToken" class="github-token-badge">
          <span class="badge success">Токен установлен - доступ к приватным репо</span>
        </div>
        <div v-else class="github-token-badge">
          <span class="badge warning">Только публичные репо</span>
          <a href="/settings" class="link">Добавить токен в настройках</a>
        </div>

        <div class="github-input">
          <input
            v-model="githubUsername"
            placeholder="username"
            @keyup.enter="analyzeGithub"
          />
          <button
            @click="analyzeGithub"
            :disabled="analyzingGithub || !githubUsername"
          >
            {{ analyzingGithub ? 'Анализ...' : 'Анализировать' }}
          </button>
        </div>

        <div v-if="githubAnalysisResult" class="analysis-result">
          <p>
            Проанализировано репозиториев: <strong>{{ githubAnalysisResult.repos_analyzed }}</strong>
            <span v-if="githubAnalysisResult.private_repos_analyzed > 0">
              (из них приватных: {{ githubAnalysisResult.private_repos_analyzed }})
            </span>
          </p>
        </div>

        <div v-if="githubSkills.length > 0" class="skills-found">
          <strong>Найденные навыки:</strong>
          <div class="skills-tags">
            <span v-for="skill in githubSkills" :key="skill" class="skill-tag">
              {{ skill }}
            </span>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <button class="primary" @click="nextStep">
          Далее →
        </button>
      </div>
    </div>

    <!-- Step 2: Search Config -->
    <div v-if="currentStep === 2" class="step-content">
      <h2>Шаг 2: Настройка поиска</h2>

      <div class="card">
        <h3>Города</h3>
        <div class="selection-grid">
          <label
            v-for="city in cities"
            :key="city.id"
            class="selection-item"
            :class="{ selected: selectedCities.includes(city.id) }"
          >
            <input
              type="checkbox"
              :checked="selectedCities.includes(city.id)"
              @change="toggleCity(city.id)"
            />
            <span>{{ city.name }}</span>
          </label>
        </div>
      </div>

      <div class="card">
        <h3>Специализации</h3>
        <div v-if="loadingSpecs" class="loading">Загрузка...</div>
        <div v-else class="selection-grid specializations">
          <label
            v-for="spec in specializations"
            :key="spec.id"
            class="selection-item"
            :class="{ selected: selectedSpecs.includes(spec.id) }"
          >
            <input
              type="checkbox"
              :checked="selectedSpecs.includes(spec.id)"
              @change="toggleSpec(spec.id)"
            />
            <span>{{ spec.name }}</span>
            <span class="count" v-if="spec.count">({{ spec.count }})</span>
          </label>
        </div>
      </div>

      <div class="step-actions">
        <button class="secondary" @click="prevStep">← Назад</button>
        <button class="primary" @click="startAutomation">
          Запустить автоматизацию 🚀
        </button>
      </div>
    </div>

    <!-- Step 3: Vacancy Loading -->
    <div v-if="currentStep === 3" class="step-content">
      <h2>Шаг 3: Загрузка вакансий</h2>

      <div class="card progress-card">
        <div class="progress-info">
          <span class="big-number">{{ vacanciesLoaded }}</span>
          <span class="label">вакансий загружено</span>
        </div>
        <div v-if="vacanciesTotal > 0" class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (vacanciesLoaded / vacanciesTotal * 100) + '%' }"
          ></div>
        </div>
        <p class="status-text" v-if="automationStatus?.message">
          {{ automationStatus.message }}
        </p>
      </div>
    </div>

    <!-- Step 4: Analysis -->
    <div v-if="currentStep === 4" class="step-content">
      <h2>Шаг 4: Анализ и рекомендации</h2>

      <div class="card progress-card">
        <div class="progress-info">
          <span class="big-number">{{ analyzedCount }}</span>
          <span class="label">вакансий проанализировано</span>
        </div>
      </div>

      <div v-if="recommendations.length > 0" class="card">
        <h3>Рекомендованные вакансии</h3>
        <div class="recommendations-list">
          <div v-for="rec in recommendations" :key="rec.vacancy_id" class="recommendation-item">
            <div class="rec-header">
              <strong>{{ rec.title }}</strong>
              <span class="match-score">{{ rec.match_score }}%</span>
            </div>
            <p class="company">{{ rec.company }}</p>
            <p class="reason">{{ rec.reason }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Step 5: Resume Generation & Apply -->
    <div v-if="currentStep === 5" class="step-content">
      <h2>Шаг 5: Резюме и отклики</h2>

      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-number">{{ generatedCount }}</span>
          <span class="stat-label">резюме создано</span>
        </div>
        <div class="stat-card">
          <span class="stat-number">{{ appliedCount }}</span>
          <span class="stat-label">откликов отправлено</span>
        </div>
      </div>

      <div v-if="automationStatus?.status === 'completed'" class="card success-card">
        <h3>✅ Автоматизация завершена!</h3>
        <p>Создано {{ generatedCount }} резюме, отправлено {{ appliedCount }} откликов.</p>
        <button class="primary" @click="currentStep = 1">Начать заново</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.automation-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  margin: 0 0 8px;
}

.subtitle {
  color: var(--text-secondary);
  margin: 0;
}

/* Progress Steps */
.steps-progress {
  display: flex;
  justify-content: space-between;
  margin-bottom: 32px;
  padding: 0 20px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 16px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: var(--border);
}

.step.completed:not(:last-child)::after {
  background: var(--primary);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--bg-secondary);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  z-index: 1;
  transition: all 0.2s;
}

.step.active .step-number {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.step.completed .step-number {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

.step-title {
  font-size: 12px;
  margin-top: 8px;
  color: var(--text-secondary);
  text-align: center;
}

.step.active .step-title {
  color: var(--text);
  font-weight: 500;
}

/* Status Banner */
.status-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.status-banner.running {
  background: #DBEAFE;
  border: 1px solid #3B82F6;
}

.status-icon {
  font-size: 24px;
}

.status-info {
  flex: 1;
}

.status-info strong {
  display: block;
}

.status-info p {
  margin: 4px 0 0;
  font-size: 14px;
  color: var(--text-secondary);
}

/* Cards */
.card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.card h3 {
  margin: 0 0 16px;
  font-size: 16px;
}

/* Selection Grid */
.selection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.selection-grid.specializations {
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}

.selection-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.selection-item:hover {
  border-color: var(--primary);
}

.selection-item.selected {
  background: #EBF5FF;
  border-color: var(--primary);
}

.selection-item input {
  display: none;
}

.selection-item .count {
  color: var(--text-secondary);
  font-size: 12px;
  margin-left: auto;
}

/* GitHub Input */
.github-input {
  display: flex;
  gap: 8px;
}

.github-input input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
}

.skills-found {
  margin-top: 16px;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.skill-tag {
  background: #E0F2FE;
  color: #0369A1;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 13px;
}

/* GitHub Token Badge */
.github-token-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.github-token-badge .badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.badge.success {
  background: #D1FAE5;
  color: #059669;
}

.badge.warning {
  background: #FEF3C7;
  color: #B45309;
}

.github-token-badge .link {
  font-size: 12px;
  color: var(--primary);
}

.analysis-result {
  margin-top: 12px;
  padding: 10px 12px;
  background: #F0FDF4;
  border-radius: 8px;
  font-size: 13px;
}

.analysis-result p {
  margin: 0;
}

/* Resume List */
.resume-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resume-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.resume-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.resume-info .status {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Progress Card */
.progress-card {
  text-align: center;
  padding: 40px;
}

.progress-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.big-number {
  font-size: 48px;
  font-weight: 700;
  color: var(--primary);
}

.progress-bar {
  width: 100%;
  max-width: 400px;
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  margin: 16px auto;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.3s;
}

.status-text {
  color: var(--text-secondary);
  margin-top: 16px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 36px;
  font-weight: 700;
  color: var(--primary);
}

.stat-label {
  color: var(--text-secondary);
  font-size: 14px;
}

/* Recommendations */
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.rec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.match-score {
  background: #10B981;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.company {
  color: var(--text-secondary);
  margin: 4px 0;
  font-size: 14px;
}

.reason {
  font-size: 13px;
  margin: 8px 0 0;
}

/* Success Card */
.success-card {
  text-align: center;
  background: #ECFDF5;
  border-color: #10B981;
}

/* Step Actions */
.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.step-actions button:only-child {
  margin-left: auto;
}

/* Buttons */
button {
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

button.primary {
  background: var(--primary);
  color: white;
}

button.primary:hover {
  opacity: 0.9;
}

button.secondary {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
}

button.danger {
  background: #EF4444;
  color: white;
}

button.small {
  padding: 6px 12px;
  font-size: 13px;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Utils */
.loading {
  color: var(--text-secondary);
  padding: 20px;
  text-align: center;
}

.empty {
  color: var(--text-secondary);
  padding: 20px;
  text-align: center;
}

.hint {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0 0 12px;
}
</style>
