// Pinia-tietovarasto käyttäjän autentikaatiolle ja profiilille
import { defineStore } from 'pinia'
import { registerUser, fetchUser, loginUser, updateUserProfile } from '@/services/authService'
import { useUserChatStore } from '@/stores/userChatStore'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null, // Käyttäjän tiedot
    token: localStorage.getItem('token') || null, // JWT-token
    loading: false, // Lataustila
  }),

  getters: {
    getCurrentUserID: (state) => state.user?.id || null, // Palauttaa käyttäjän ID:n
    isPatient: (state) => state.user?.role === "patient", // Onko potilas
    isProfessional: (state) => state.user?.role === "professional", // Onko ammattilainen
    isAuthenticated: (state) => !!state.token // Onko kirjautunut
  },

  actions: {
    // Käyttäjän rekisteröinti
    async register(formData) {
      this.loading = true
      try {
        const data = await registerUser(formData)

        this.user = data.user
        this.token = data.token

        localStorage.setItem("token", data.token)
      } catch (error) {
        console.log("Registration failed: ", error)
        throw error
      } finally {
        this.loading = false
      }
    },
    // Kirjautuminen
    async login(email, password) {
      this.loading = true

      try {
        const data = await loginUser(email, password)
        this.user = data.user
        this.token = data.token

        localStorage.setItem('token', data.token)

        // Chatin alustaminen kirjautumisen jälkeen
        const userChatStore = useUserChatStore();
        await userChatStore.initializeChats(true);
      } catch (error) {
        console.error("Login failed:", error)
        throw error
      } finally {
        this.loading = false
      }
    },
    // Uloskirjautuminen
    async logout() {
      this.user = null
      this.token = null
      localStorage.removeItem("token")
      // Chatin tyhjennys uloskirjautuessa
      const userChatStore = useUserChatStore();
      userChatStore.clearChats();
    },
    // Käyttäjän tietojen haku
    async fetchUser() {
      if (!this.token) return

      this.loading = true
      try {
        const data = await fetchUser(this.token)
        this.user = data

      } catch (error) {
        console.error("Failed to fetch user profile:", error)
      } finally {
        this.loading = false
      }
    },
    // Käyttäjän profiilin päivitys
    async updateProfile(formData) {
      this.loading = true

      try {
        const updatedUser = await updateUserProfile(formData);
        this.user = updatedUser
      } catch (error) {
        console.error("Profile update failed:", error)
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})
