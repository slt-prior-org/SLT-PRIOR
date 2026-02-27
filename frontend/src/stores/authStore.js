import { defineStore } from 'pinia'
import { registerUser, fetchUser, loginUser, logoutUser, updateUserProfile } from '@/services/authService'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
    loading: false,
  }),

  getters: {
    getCurrentUserID: (state) => state.user?.id || null,
    isPatient: (state) => state.user?.role === "patient",
    isProfessional: (state) => state.user?.role === "professional",
    isAuthenticated: (state) => !!state.token
  },

  actions: {
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
    async login(email, password) {
      this.loading = true

      try {
        const data = await loginUser(email, password)
        this.user = data.user
        this.token = data.token

        localStorage.setItem('token', data.token)

      } catch (error) {
        console.error("Login failed:", error)
        throw error
      } finally {
        this.loading = false
      }
    },
    async logout() {
      try {
        await logoutUser()
        this.user = null
        this.token = null
        localStorage.removeItem("token")
      } catch (error) {
        console.log("Logout failed on backend:", error)
      }
    },
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
    async updateProfile(formData) {
      this.loading = true

      try {
        const updatedUser = await updateUserProfile(formData)
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
