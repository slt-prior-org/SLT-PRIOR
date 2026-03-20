// Pinia-tietovarasto chatille ja viestien hallinnalle
import { defineStore } from "pinia"
import {
  addChat,
  fetchAllUserChats,
  sendUserMessage
} from "@/services/userChatService"

export const useUserChatStore = defineStore("userChat", {
  state: () => ({
    userChats: [], // Kaikki käyttäjän chatit
    activeChatId: null, // Aktiivisen chatin ID
    isLoaded: false, // Onko chatit ladattu
    isSending: false // Estää viestien spam/race condition
  }),

  getters: {
    getUserChats: (state) => state.userChats, // Palauttaa kaikki chatit

    getActiveChat(state) {
      if (!state.activeChatId) return null
      return state.userChats.find(chat => chat.id === state.activeChatId) || null // Palauttaa aktiivisen chatin
    }
  },

  actions: {
    setActiveChat(chatId) {
      this.activeChatId = chatId // Asettaa aktiivisen chatin
    },

    clearChats() {
      this.userChats = [] // Tyhjentää chatit
      this.activeChatId = null // Tyhjentää aktiivisen chatin
      this.isLoaded = false // Resetoi lataustilan
    },

    // Chatien haku ja alustaminen
    async initializeChats(force = false) {
      if (this.isLoaded && !force) return

      try {
        const chats = await fetchAllUserChats()

        // Varmistaa että jokaisella chatilla on messages-taulukko
        this.userChats = chats.map(chat => ({
          ...chat,
          messages: chat.messages || []
        }))

        // Aseta ensimmäinen chat aktiiviseksi jos ei ole
        if (!this.activeChatId && this.userChats.length > 0) {
          this.activeChatId = this.userChats[0].id
        }

        this.isLoaded = true
      } catch (error) {
        console.error("Failed to initialize user chats:", error)
        throw error
      }
    },

    // Uuden chatin luonti
    async createChat() {
      try {
        const newChat = await addChat()

        const chat = {
          ...newChat,
          messages: newChat.messages || []
        }

        this.userChats.push(chat)
        this.activeChatId = chat.id

        return chat
      } catch (error) {
        console.error("Failed to create chat:", error)
        throw error
      }
    },

    // Viestin lähetys chatissa (vain tila ja API, ei UI)
    async addUserMessage(message) {
      const chat = this.userChats.find(c => c.id === this.activeChatId)
      if (!chat) return

      if (this.isSending) return // Estää useat lähetykset

      if (["waiting_for_professional", "in_progress"].includes(chat.status)) {
        throw new Error("Chat is locked") // Estää viestit tietyissä tiloissa
      }

      this.isSending = true

      const messageIndex = chat.messages.push({
        text: message,
        from: "self",
        classification: undefined
      }) - 1

      try {
        const data = await sendUserMessage(chat.id, { message })

        // Päivitetään viestin luokitus
        if (chat.messages[messageIndex]) {
          chat.messages[messageIndex].classification = data.classification
        }

        // Lisätään botin vastaus
        if (data.reply) {
          chat.messages.push({
            text: data.reply,
            from: "other",
            classification: data.classification
          })
        }

        // Päivitetään chatin status tarvittaessa
        if (data.classification === "needs_review") {
          chat.status = "waiting_for_professional"
        }

        if (data.classification === "emergency") {
          console.warn("Emergency message detected")
        }

      } catch (error) {
        console.error("Failed to send user message:", error)

        throw error
      } finally {
        this.isSending = false
      }
    }
  }
})