<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { settingsApi, type Prompts } from '@/api/settings'
import { hhApi, type HHResume } from '@/api/vacancies'
import { useAuthStore } from '@/stores/auth'
import type { Settings } from '@/types'

const authStore = useAuthStore()

const settings = ref<Settings | null>(null)
const loading = ref(false)
const saving = ref(false)

const llmProvider = ref<'claude' | 'openai'>('openai')
const llmModel = ref('')
const claudeKey = ref('')
const openaiKey = ref('')

// HH Resumes
const hhResumes = ref<HHResume[]>([])
const loadingResumes = ref(false)
const importingResumeId = ref<string | null>(null)

// Prompts
const prompts = ref<Prompts | null>(null)
const loadingPrompts = ref(false)
const savingPrompts = ref(false)
const showPromptSection = ref(false)

const availableModels = computed(() => {
  if (!settings.value) return []
  return settings.value.available_models[llmProvider.value] || []
})

// When provider changes, reset model to first available
watch(llmProvider, () => {
  if (availableModels.value.length > 0) {
    llmModel.value = availableModels.value[0]
  }
})

onMounted(async () => {
  loading.value = true
  try {
    settings.value = await settingsApi.get()
    llmProvider.value = settings.value.llm_provider
    llmModel.value = settings.value.llm_model || settings.value.available_models[llmProvider.value]?.[0] || ''
  } finally {
    loading.value = false
  }
})

async function saveSettings() {
  saving.value = true
  try {
    const data: any = {
      llm_provider: llmProvider.value,
      llm_model: llmModel.value,
    }
    if (claudeKey.value) data.claude_api_key = claudeKey.value
    if (openaiKey.value) data.openai_api_key = openaiKey.value

    settings.value = await settingsApi.update(data)
    claudeKey.value = ''
    openaiKey.value = ''
    alert('Настройки сохранены!')
  } catch {
    alert('Ошибка сохранения')
  } finally {
    saving.value = false
  }
}

async function loadHHResumes() {
  loadingResumes.value = true
  try {
    const result = await hhApi.getMyResumes()
    hhResumes.value = result.resumes
  } catch (error: any) {
    if (error.response?.status === 401) {
      alert('Необходимо авторизоваться в HH.ru')
    } else {
      alert('Ошибка загрузки резюме с HH.ru')
    }
  } finally {
    loadingResumes.value = false
  }
}

async function importResume(resumeId: string) {
  importingResumeId.value = resumeId
  try {
    const result = await hhApi.importResume(resumeId)
    alert(`Резюме "${result.title}" успешно импортировано!`)
  } catch (error: any) {
    alert(error.response?.data?.detail || 'Ошибка импорта резюме')
  } finally {
    importingResumeId.value = null
  }
}

// Prompts functions
async function loadPrompts() {
  loadingPrompts.value = true
  try {
    prompts.value = await settingsApi.getPrompts()
    showPromptSection.value = true
  } catch {
    alert('Ошибка загрузки промптов')
  } finally {
    loadingPrompts.value = false
  }
}

async function savePrompts() {
  if (!prompts.value) return
  savingPrompts.value = true
  try {
    prompts.value = await settingsApi.updatePrompts(prompts.value)
    alert('Промпты сохранены!')
  } catch {
    alert('Ошибка сохранения промптов')
  } finally {
    savingPrompts.value = false
  }
}

async function resetPrompts() {
  if (!confirm('Сбросить все промпты к значениям по умолчанию?')) return
  try {
    await settingsApi.resetPrompts()
    prompts.value = await settingsApi.getPrompts()
    alert('Промпты сброшены!')
  } catch {
    alert('Ошибка сброса промптов')
  }
}
</script>

<template>
  <div class="settings-view">
    <div class="page-header">
      <h1>Настройки</h1>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>

    <template v-else>
      <!-- HH Connection -->
      <div class="section">
        <h2>HeadHunter</h2>
        <div class="card">
          <div v-if="authStore.status?.hh_connected" class="hh-connected">
            <span class="status-badge success">Подключено</span>
            <p>HH.ru аккаунт подключён (ID: {{ authStore.status.hh_user_id }})</p>

            <!-- Import Resumes Section -->
            <div class="hh-resumes-section">
              <div class="resumes-header">
                <h4>Импорт резюме</h4>
                <button
                  class="secondary small"
                  @click="loadHHResumes"
                  :disabled="loadingResumes"
                >
                  {{ loadingResumes ? 'Загрузка...' : 'Загрузить мои резюме' }}
                </button>
              </div>

              <div v-if="hhResumes.length" class="resumes-list">
                <div v-for="resume in hhResumes" :key="resume.id" class="resume-item">
                  <div class="resume-info">
                    <span class="resume-title">{{ resume.title }}</span>
                    <span class="resume-status">{{ resume.status }}</span>
                    <span class="resume-views">{{ resume.total_views }} просмотров</span>
                  </div>
                  <button
                    class="primary small"
                    @click="importResume(resume.id)"
                    :disabled="importingResumeId === resume.id"
                  >
                    {{ importingResumeId === resume.id ? 'Импорт...' : 'Импортировать' }}
                  </button>
                </div>
              </div>
            </div>

            <button class="secondary" @click="authStore.logout">Отключить</button>
          </div>
          <div v-else class="hh-disconnected">
            <p>Подключите аккаунт HH.ru для поиска вакансий и импорта резюме</p>
            <button class="primary" @click="authStore.loginHH">
              Подключить HH.ru
            </button>
          </div>
        </div>
      </div>

      <!-- LLM Settings -->
      <div class="section">
        <h2>LLM провайдер</h2>
        <div class="card">
          <div class="form-group">
            <label>Провайдер</label>
            <div class="radio-group">
              <label class="radio-option">
                <input type="radio" v-model="llmProvider" value="claude" />
                <span>Claude (Anthropic)</span>
                <span v-if="settings?.has_claude_key" class="badge success">Ключ установлен</span>
              </label>
              <label class="radio-option">
                <input type="radio" v-model="llmProvider" value="openai" />
                <span>OpenAI</span>
                <span v-if="settings?.has_openai_key" class="badge success">Ключ установлен</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>Модель</label>
            <select v-model="llmModel" class="model-select">
              <option v-for="model in availableModels" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
            <p class="hint" v-if="llmModel">
              Текущая модель: <strong>{{ llmModel }}</strong>
            </p>
          </div>

          <div class="form-group" v-if="llmProvider === 'claude'">
            <label>Claude API Key</label>
            <input
              v-model="claudeKey"
              type="password"
              placeholder="sk-ant-..."
            />
          </div>

          <div class="form-group" v-if="llmProvider === 'openai'">
            <label>OpenAI API Key</label>
            <input
              v-model="openaiKey"
              type="password"
              placeholder="sk-..."
            />
          </div>

          <button
            class="primary"
            @click="saveSettings"
            :disabled="saving"
          >
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </div>

      <!-- Prompts Settings -->
      <div class="section">
        <h2>Настройка промптов</h2>
        <div class="card">
          <div v-if="!showPromptSection" class="prompts-intro">
            <p>Настройте промпты для интервью и добавьте скрытые инструкции в резюме для обхода AI-скринеров.</p>
            <button
              class="secondary"
              @click="loadPrompts"
              :disabled="loadingPrompts"
            >
              {{ loadingPrompts ? 'Загрузка...' : 'Редактировать промпты' }}
            </button>
          </div>

          <template v-else-if="prompts">
            <div class="form-group">
              <label>Системный промпт интервью</label>
              <textarea
                v-model="prompts.interview_system"
                rows="6"
                placeholder="Системные инструкции для LLM при проведении интервью..."
              ></textarea>
              <p class="hint">Определяет поведение ассистента во время интервью</p>
            </div>

            <div class="form-group">
              <label>Первое сообщение интервью</label>
              <textarea
                v-model="prompts.interview_first_message"
                rows="4"
                placeholder="Приветственное сообщение для начала интервью..."
              ></textarea>
              <p class="hint">Сообщение, которое пользователь видит в начале нового интервью</p>
            </div>

            <div class="form-group injection-section">
              <div class="injection-header">
                <label>Prompt Injection для резюме</label>
                <label class="toggle">
                  <input type="checkbox" v-model="prompts.prompt_injection_enabled" />
                  <span class="toggle-slider"></span>
                  <span class="toggle-label">{{ prompts.prompt_injection_enabled ? 'Включено' : 'Выключено' }}</span>
                </label>
              </div>
              <textarea
                v-model="prompts.prompt_injection"
                rows="6"
                placeholder="Скрытый текст для AI-скринеров работодателей..."
                :disabled="!prompts.prompt_injection_enabled"
              ></textarea>
              <p class="hint warning">
                Этот текст будет добавлен в резюме в виде HTML-комментария для влияния на AI-системы отбора резюме.
                Демонстрирует ваши знания LLM и prompt engineering.
              </p>
            </div>

            <div class="prompts-actions">
              <button
                class="primary"
                @click="savePrompts"
                :disabled="savingPrompts"
              >
                {{ savingPrompts ? 'Сохранение...' : 'Сохранить промпты' }}
              </button>
              <button class="secondary" @click="resetPrompts">
                Сбросить по умолчанию
              </button>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.settings-view {
  max-width: 600px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

.section {
  margin-bottom: 32px;
}

.section h2 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.hh-connected,
.hh-disconnected {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}

.hh-connected p,
.hh-disconnected p {
  color: var(--text-secondary);
  font-size: 14px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.success {
  background: #D1FAE5;
  color: #059669;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-option input {
  width: auto;
}

.badge.success {
  background: #D1FAE5;
  color: #059669;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 11px;
  margin-left: 8px;
}

.model-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: white;
}

.hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.hint strong {
  color: var(--primary);
}

/* HH Resumes Import */
.hh-resumes-section {
  width: 100%;
  margin: 16px 0;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.resumes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.resumes-header h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.resumes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resume-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid var(--border);
}

.resume-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.resume-title {
  font-weight: 500;
}

.resume-status,
.resume-views {
  font-size: 12px;
  color: var(--text-secondary);
}

button.small {
  padding: 6px 12px;
  font-size: 12px;
}

/* Prompts Section */
.prompts-intro {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.prompts-intro p {
  color: var(--text-secondary);
  font-size: 14px;
}

textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

textarea:disabled {
  background: var(--bg-secondary);
  opacity: 0.6;
}

.injection-section {
  background: var(--bg-secondary);
  padding: 16px;
  border-radius: 8px;
  margin: 16px 0;
}

.injection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.injection-header > label:first-child {
  margin-bottom: 0;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.toggle input {
  display: none;
}

.toggle-slider {
  width: 40px;
  height: 20px;
  background: var(--border);
  border-radius: 10px;
  position: relative;
  transition: background 0.2s;
}

.toggle-slider::after {
  content: '';
  position: absolute;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.toggle input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle input:checked + .toggle-slider::after {
  transform: translateX(20px);
}

.toggle-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.hint.warning {
  color: #B45309;
  background: #FEF3C7;
  padding: 8px 12px;
  border-radius: 6px;
  margin-top: 8px;
}

.prompts-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
</style>
