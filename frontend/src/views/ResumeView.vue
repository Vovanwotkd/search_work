<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { resumesApi } from '@/api/resumes'
import type { BaseResume, ResumeVariation } from '@/types'

const baseResume = ref<BaseResume | null>(null)
const variations = ref<ResumeVariation[]>([])
const loading = ref(false)
const generating = ref(false)

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  try {
    baseResume.value = await resumesApi.getBase()
    variations.value = await resumesApi.listVariations()
  } finally {
    loading.value = false
  }
}

async function generateBaseResume() {
  generating.value = true
  try {
    baseResume.value = await resumesApi.createBase()
    alert('Базовое резюме создано!')
  } catch {
    alert('Ошибка создания резюме. Убедитесь что профиль создан.')
  } finally {
    generating.value = false
  }
}

async function generateCoverLetter(variationId: number) {
  try {
    const result = await resumesApi.generateCoverLetter(variationId)
    const variation = variations.value.find(v => v.id === variationId)
    if (variation) {
      variation.cover_letter = result.cover_letter
    }
    alert('Сопроводительное письмо создано!')
  } catch {
    alert('Ошибка создания письма')
  }
}

async function deleteVariation(id: number) {
  if (!confirm('Удалить это резюме?')) return
  try {
    await resumesApi.deleteVariation(id)
    variations.value = variations.value.filter(v => v.id !== id)
  } catch {
    alert('Ошибка удаления')
  }
}
</script>

<template>
  <div class="resume-view">
    <div class="page-header">
      <h1>Резюме</h1>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>

    <template v-else>
      <!-- Base Resume Section -->
      <div class="section">
        <h2>Базовое резюме</h2>

        <div v-if="!baseResume" class="card empty-state">
          <p>Базовое резюме ещё не создано</p>
          <button
            class="primary"
            @click="generateBaseResume"
            :disabled="generating"
          >
            {{ generating ? 'Создание...' : 'Создать из профиля' }}
          </button>
        </div>

        <div v-else class="card">
          <h3>{{ baseResume.title }}</h3>
          <details>
            <summary>Показать содержимое</summary>
            <pre>{{ JSON.stringify(baseResume.content, null, 2) }}</pre>
          </details>
        </div>
      </div>

      <!-- Variations Section -->
      <div class="section">
        <h2>Адаптированные резюме ({{ variations.length }})</h2>

        <div v-if="!variations.length" class="card empty-state">
          <p>Нет адаптированных резюме. Создайте их из раздела "Вакансии".</p>
        </div>

        <div v-else class="variations-list">
          <div
            v-for="variation in variations"
            :key="variation.id"
            class="card variation-card"
          >
            <div class="variation-header">
              <h3>{{ variation.title }}</h3>
              <span class="badge" :class="variation.status">
                {{ variation.status === 'draft' ? 'Черновик' : variation.status === 'published' ? 'Опубликовано' : 'Архив' }}
              </span>
            </div>

            <div v-if="variation.adaptations" class="adaptations">
              <strong>Адаптации:</strong>
              <ul>
                <li v-for="(adapt, i) in (variation.adaptations as unknown as any[])" :key="i">
                  {{ adapt.field }}: {{ adapt.reason }}
                </li>
              </ul>
            </div>

            <div v-if="variation.cover_letter" class="cover-letter">
              <strong>Сопроводительное письмо:</strong>
              <p>{{ variation.cover_letter }}</p>
            </div>

            <div class="variation-actions">
              <button
                v-if="!variation.cover_letter"
                class="secondary"
                @click="generateCoverLetter(variation.id)"
              >
                Создать письмо
              </button>
              <button class="secondary" @click="deleteVariation(variation.id)">
                Удалить
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.resume-view {
  max-width: 900px;
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

.empty-state {
  text-align: center;
  padding: 40px;
}

.empty-state p {
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

details {
  margin-top: 8px;
}

summary {
  cursor: pointer;
  color: var(--primary);
  font-size: 14px;
}

pre {
  margin-top: 12px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 300px;
}

.variations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.variation-card {
  padding: 20px;
}

.variation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.badge.draft {
  background: #FEF3C7;
  color: #D97706;
}

.badge.published {
  background: #D1FAE5;
  color: #059669;
}

.adaptations {
  margin-bottom: 16px;
  font-size: 14px;
}

.adaptations ul {
  margin-top: 8px;
  padding-left: 20px;
}

.adaptations li {
  margin-bottom: 4px;
}

.cover-letter {
  margin-bottom: 16px;
  font-size: 14px;
}

.cover-letter p {
  margin-top: 8px;
  padding: 12px;
  background: var(--bg);
  border-radius: 8px;
  white-space: pre-wrap;
}

.variation-actions {
  display: flex;
  gap: 12px;
}

.variation-actions button {
  padding: 8px 16px;
  font-size: 13px;
}
</style>
