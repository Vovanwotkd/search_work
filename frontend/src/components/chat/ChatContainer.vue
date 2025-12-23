<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'

const chatStore = useChatStore()
const messagesContainer = ref<HTMLElement | null>(null)

onMounted(() => {
  chatStore.loadSession()
})

// Auto-scroll to bottom when new messages arrive
watch(
  () => chatStore.messages.length,
  async () => {
    await nextTick()
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }
)

async function handleSend(content: string) {
  await chatStore.sendMessage(content)
}

async function handleComplete() {
  try {
    await chatStore.completeInterview()
    alert('Интервью завершено! Профиль создан.')
  } catch (error) {
    alert('Ошибка при завершении интервью')
  }
}

async function handleReset() {
  if (confirm('Начать интервью заново? Текущий прогресс будет сохранён в истории.')) {
    await chatStore.resetSession()
  }
}
</script>

<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>Интервью</h2>
      <div class="chat-actions">
        <button
          v-if="!chatStore.isCompleted && chatStore.messages.length > 4"
          class="primary"
          @click="handleComplete"
          :disabled="chatStore.loading"
        >
          Завершить
        </button>
        <button class="secondary" @click="handleReset" :disabled="chatStore.loading">
          Начать заново
        </button>
      </div>
    </div>

    <div v-if="chatStore.loading && !chatStore.messages.length" class="chat-loading">
      Загрузка...
    </div>

    <div v-else ref="messagesContainer" class="messages-container">
      <ChatMessage
        v-for="(message, index) in chatStore.messages"
        :key="index"
        :message="message"
      />

      <div v-if="chatStore.sending" class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <div v-if="chatStore.isCompleted" class="completed-banner">
      Интервью завершено. Перейдите в раздел "Профиль" чтобы посмотреть результат.
    </div>

    <ChatInput
      v-if="!chatStore.isCompleted"
      @send="handleSend"
      :disabled="chatStore.sending"
    />
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 48px);
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.chat-header h2 {
  font-size: 18px;
  font-weight: 600;
}

.chat-actions {
  display: flex;
  gap: 8px;
}

.chat-actions button {
  padding: 8px 16px;
  font-size: 13px;
}

.chat-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--bg);
  border-radius: 12px;
  width: fit-content;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.completed-banner {
  padding: 16px 20px;
  background: #D1FAE5;
  color: #059669;
  text-align: center;
  font-size: 14px;
}
</style>
