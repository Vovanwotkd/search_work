import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatApi } from '@/api/chat'
import type { ChatSession } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const session = ref<ChatSession | null>(null)
  const loading = ref(false)
  const sending = ref(false)

  const messages = computed(() => session.value?.messages || [])
  const isCompleted = computed(() => session.value?.status === 'completed')

  async function loadSession() {
    loading.value = true
    try {
      session.value = await chatApi.getSession()
    } catch (error) {
      console.error('Failed to load session:', error)
    } finally {
      loading.value = false
    }
  }

  async function sendMessage(content: string) {
    if (!content.trim() || sending.value) return

    sending.value = true
    try {
      session.value = await chatApi.sendMessage(content)
    } catch (error) {
      console.error('Failed to send message:', error)
      throw error
    } finally {
      sending.value = false
    }
  }

  async function completeInterview() {
    loading.value = true
    try {
      const result = await chatApi.complete()
      if (session.value) {
        session.value.status = 'completed'
      }
      return result
    } finally {
      loading.value = false
    }
  }

  async function resetSession() {
    loading.value = true
    try {
      session.value = await chatApi.reset()
    } finally {
      loading.value = false
    }
  }

  return {
    session,
    messages,
    isCompleted,
    loading,
    sending,
    loadSession,
    sendMessage,
    completeInterview,
    resetSession,
  }
})
