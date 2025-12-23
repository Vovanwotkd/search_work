<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  send: [content: string]
}>()

defineProps<{
  disabled?: boolean
}>()

const input = ref('')

function handleSubmit() {
  if (!input.value.trim()) return
  emit('send', input.value)
  input.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}
</script>

<template>
  <div class="chat-input-container">
    <textarea
      v-model="input"
      placeholder="Напишите сообщение..."
      rows="1"
      :disabled="disabled"
      @keydown="handleKeydown"
    />
    <button
      class="send-button"
      :disabled="disabled || !input.trim()"
      @click="handleSubmit"
    >
      ➤
    </button>
  </div>
</template>

<style scoped>
.chat-input-container {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--border);
}

textarea {
  flex: 1;
  resize: none;
  min-height: 44px;
  max-height: 120px;
  padding: 12px 16px;
}

.send-button {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary);
  color: white;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.send-button:disabled {
  background: var(--border);
  cursor: not-allowed;
}
</style>
