<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const navItems = [
  { path: '/chat', icon: '💬', label: 'Интервью' },
  { path: '/profile', icon: '👤', label: 'Профиль' },
  { path: '/automation', icon: '🚀', label: 'Автоматизация' },
  { path: '/search', icon: '📥', label: 'Поиск и экспорт' },
  { path: '/vacancies', icon: '🔍', label: 'Вакансии' },
  { path: '/resumes', icon: '📄', label: 'Резюме' },
  { path: '/settings', icon: '⚙️', label: 'Настройки' },
]
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1 class="logo">JS</h1>
      <span class="logo-text">Job Search</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: route.path === item.path }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div v-if="authStore.status?.hh_connected" class="hh-status connected">
        <span class="status-dot"></span>
        HH.ru подключён
      </div>
      <div v-else class="hh-status">
        <span class="status-dot disconnected"></span>
        HH.ru не подключён
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
}

.logo {
  width: 40px;
  height: 40px;
  background: var(--primary);
  color: white;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
}

.logo-text {
  font-weight: 600;
  font-size: 16px;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--text-secondary);
  transition: all 0.2s;
}

.nav-item:hover {
  background: var(--bg);
  color: var(--text);
}

.nav-item.active {
  background: #EEF2FF;
  color: var(--primary);
}

.nav-icon {
  font-size: 18px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

.sidebar-footer {
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.hh-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  padding: 8px 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
}

.status-dot.disconnected {
  background: var(--secondary);
}
</style>
