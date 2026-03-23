import { defineStore } from "pinia"
import { useUserChatStore } from "@/stores/userChatStore"
import {
  registerUser,
  fetchUser,
  loginUser,
  updateUserProfile,
} from "@/services/authService"
import { chatSocket } from "@/services/chatSocket"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    token: sessionStorage.getItem("token") || null,
    loading: false,
  }),

  getters: {
    getCurrentUserID: (state) => state.user?.id || null,
    isPatient: (state) => state.user?.role === "patient",
    isProfessional: (state) => state.user?.role === "professional",
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    async register(formData) {
      this.loading = true
      try {
        const data = await registerUser(formData)

        this.user = data.user
        this.token = data.token

        sessionStorage.setItem("token", data.token)

        // Alustetaan käyttäjän chat historia
        const chatStore = useUserChatStore()
        await chatStore.initializeChats()

        // Jos Pinian store ei sisällä aktiivista chattia, luodaan uusi
        if (!chatStore.activeChat) {
          console.log("käyttäjä reksiteröityi sovellukseen, luodaan tyhjä chat")
          await chatStore.createChat()
        }
      } catch (error) {
        console.error("Registration failed:", error)
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

        sessionStorage.setItem("token", data.token)

        // Alustetaan käyttäjän chat historia
        const chatStore = useUserChatStore()
        await chatStore.initializeChats()

        // Jos Pinian store ei sisällä aktiivista chattia, luodaan uusi
        if (!chatStore.activeChat) {
          console.log("käyttäjä kirjautui sisään, luodaan tyhjä chat")
          await chatStore.createChat()
        }
      } catch (error) {
        console.error("Login failed:", error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async logout() {
      const userChatStore = useUserChatStore()

      // Tyhjennetään näkyvä chat heti uloskirjautuessa
      userChatStore.clearChats()
      this.user = null
      this.token = null

      // Suljetaan WebSocket yhteys
      chatSocket.disconnect()

      sessionStorage.removeItem("token")
    },

    async fetchUser() {
      if (!this.token) return

      this.loading = true

      try {
        const data = await fetchUser()
        this.user = data
      } catch (error) {
        console.error("Käyttäjän tietojen haku epäonnistui:", error)
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
        console.error("Profiilin päivitys epäonnistui:", error)
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})
