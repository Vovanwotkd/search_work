<script setup lang="ts">
import { onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useRouter } from 'vue-router'

const profileStore = useProfileStore()
const router = useRouter()

onMounted(() => {
  profileStore.loadProfile()
})

function goToChat() {
  router.push('/chat')
}
</script>

<template>
  <div class="profile-view">
    <div class="page-header">
      <h1>Профиль</h1>
      <button
        v-if="profileStore.profile"
        class="secondary"
        @click="profileStore.regenerateProfile"
        :disabled="profileStore.loading"
      >
        Обновить из интервью
      </button>
    </div>

    <div v-if="profileStore.loading" class="loading">Загрузка...</div>

    <div v-else-if="!profileStore.profile" class="empty-state card">
      <p>Профиль ещё не создан. Пройдите интервью чтобы создать профиль.</p>
      <button class="primary" @click="goToChat">Начать интервью</button>
    </div>

    <div v-else class="profile-content">
      <!-- Position Card -->
      <div class="card">
        <h3>Позиция</h3>
        <p class="position-title">{{ profileStore.profile.preferred_position || 'Не указана' }}</p>
        <div class="profile-meta">
          <span v-if="profileStore.profile.experience_years">
            Опыт: {{ profileStore.profile.experience_years }} лет
          </span>
          <span v-if="profileStore.profile.preferred_locations?.length">
            Локация: {{ profileStore.profile.preferred_locations.join(', ') }}
          </span>
          <span v-if="profileStore.profile.preferred_salary_min || profileStore.profile.preferred_salary_max">
            Зарплата: {{ profileStore.profile.preferred_salary_min || '?' }} - {{ profileStore.profile.preferred_salary_max || '?' }} ₽
          </span>
        </div>
      </div>

      <!-- Skills Card -->
      <div class="card">
        <h3>Навыки</h3>
        <div class="skills-list">
          <span
            v-for="skill in profileStore.profile.skills"
            :key="skill"
            class="badge primary"
          >
            {{ skill }}
          </span>
          <span v-if="!profileStore.profile.skills?.length" class="no-data">
            Навыки не указаны
          </span>
        </div>
      </div>

      <!-- Summary Card -->
      <div class="card">
        <h3>О себе</h3>
        <p class="summary">{{ profileStore.profile.summary || 'Описание не указано' }}</p>
      </div>

      <!-- Full Profile Card -->
      <div v-if="profileStore.profile.structured_profile" class="card">
        <h3>Полный профиль</h3>
        <details>
          <summary>Показать JSON</summary>
          <pre>{{ JSON.stringify(profileStore.profile.structured_profile, null, 2) }}</pre>
        </details>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-view {
  max-width: 800px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.empty-state {
  text-align: center;
  padding: 40px;
}

.empty-state p {
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  margin-bottom: 12px;
}

.position-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 12px;
}

.profile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 14px;
  color: var(--text-secondary);
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary {
  font-size: 15px;
  line-height: 1.6;
}

.no-data {
  color: var(--text-secondary);
  font-style: italic;
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
}
</style>
