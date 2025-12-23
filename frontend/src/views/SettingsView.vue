<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { settingsApi } from '@/api/settings'
import { useAuthStore } from '@/stores/auth'
import type { Settings } from '@/types'

const authStore = useAuthStore()

const settings = ref<Settings | null>(null)
const loading = ref(false)
const saving = ref(false)

const llmProvider = ref<'claude' | 'openai'>('claude')
const claudeKey = ref('')
const openaiKey = ref('')

onMounted(async () => {
  loading.value = true
  try {
    settings.value = await settingsApi.get()
    llmProvider.value = settings.value.llm_provider
  } finally {
    loading.value = false
  }
})

async function saveSettings() {
  saving.value = true
  try {
    const data: any = { llm_provider: llmProvider.value }
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
            <button class="secondary" @click="authStore.logout">Отключить</button>
          </div>
          <div v-else class="hh-disconnected">
            <p>Подключите аккаунт HH.ru для поиска вакансий и публикации резюме</p>
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
                <span>OpenAI (GPT-4)</span>
                <span v-if="settings?.has_openai_key" class="badge success">Ключ установлен</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>Claude API Key</label>
            <input
              v-model="claudeKey"
              type="password"
              placeholder="sk-ant-..."
            />
          </div>

          <div class="form-group">
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
</style>
