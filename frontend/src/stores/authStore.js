import { defineStore } from "pinia"
import { useUserChatStore } from "@/stores/userChatStore"
import {
  registerUser,
  fetchUser,
  loginUser,
  updateUserProfile,
} from "@/services/authService"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,
    token: localStorage.getItem("token") || null,
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
      this.loading = true;
      try {
        const data = await registerUser(formData);

        this.user = data.user;
        this.token = data.token;

        localStorage.setItem("token", data.token);
      } catch (error) {
        console.error("Registration failed:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async login(email, password) {
      this.loading = true;

      try {
        const data = await loginUser(email, password);

        this.user = data.user;
        this.token = data.token;

        localStorage.setItem("token", data.token);
      } catch (error) {
        console.error("Login failed:", error);
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      const userChatStore = useUserChatStore()

      // Tyhjennetään näkyvä chat heti uloskirjautuessa
      userChatStore.clearChats()
      this.user = null
      this.token = null

      localStorage.removeItem("token")
    },

    async fetchUser() {
      if (!this.token) return;

      this.loading = true

      try {
        const data = await fetchUser()
        this.user = data
      } catch (error) {
        console.error("Käyttäjän tietojen haku epäonnistui:", error)
      } finally {
        this.loading = false;
      }
    },

    async updateProfile(formData) {
      this.loading = true;

      try {
        const updatedUser = await updateUserProfile(formData);
        this.user = updatedUser;
      } catch (error) {
        console.error("Profiilin päivitys epäonnistui:", error)
        throw error
      } finally {
        this.loading = false;
      }
    },
  },
})
