import { defineStore } from 'pinia'
import { ref } from 'vue'
import { profileApi } from '@/api/profile'
import type { Profile } from '@/types'

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<Profile | null>(null)
  const loading = ref(false)

  async function loadProfile() {
    loading.value = true
    try {
      profile.value = await profileApi.get()
    } catch (error) {
      console.error('Failed to load profile:', error)
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(data: Partial<Profile>) {
    loading.value = true
    try {
      profile.value = await profileApi.update(data)
    } finally {
      loading.value = false
    }
  }

  async function regenerateProfile() {
    loading.value = true
    try {
      profile.value = await profileApi.regenerate()
    } finally {
      loading.value = false
    }
  }

  return {
    profile,
    loading,
    loadProfile,
    updateProfile,
    regenerateProfile,
  }
})
