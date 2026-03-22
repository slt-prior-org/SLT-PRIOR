import { defineStore } from "pinia"
import {
  addChat,
  fetchAllUserChats,
  fetchChat,
  sendUserMessage,
} from "@/services/userChatService"

const LOCKED_STATUSES = ["waiting_for_professional", "in_progress"]

export const useUserChatStore = defineStore("userChat", {
  state: () => ({
    userChats: [],
    activeChat: null,
    isLoaded: false,
    isSending: false,
    isLoadingChat: false,
    currentUserId: null,
  }),

  getters: {
    getUserChats: (state) => state.userChats,
    getActiveChat: (state) => state.activeChat,
    getLatestChat: (state) => state.userChats[0] || null,
    getWritableChat(state) {
      return (
        state.userChats.find((chat) => !LOCKED_STATUSES.includes(chat.status)) ||
        null
      )
    },
  },

  actions: {
    resetChatState() {
      // Tyhjennetään chat-tila, kun käyttäjä vaihtuu tai kirjautuu ulos
      this.userChats = []
      this.activeChat = null
      this.isLoaded = false
      this.isSending = false
      this.isLoadingChat = false
      this.currentUserId = null
    },

    clearChats() {
      this.resetChatState()
    },

    upsertChatSummary(chat) {
      // Päivitetään chat-listaan tuorein yhteenveto aktiivisesta chatista
      const summary = {
        id: chat.id,
        status: chat.status,
        created_at: chat.created_at,
        updated_at: chat.updated_at,
      }
      const existingIndex = this.userChats.findIndex((item) => item.id === chat.id)

      if (existingIndex >= 0) {
        this.userChats.splice(existingIndex, 1, {
          ...this.userChats[existingIndex],
          ...summary,
        })
        return
      }

      this.userChats.unshift(summary)
    },

    async initializeChats(userId = null, force = false) {
      // Nollataan vanhan käyttäjän chatit, jos tunnistautunut käyttäjä vaihtui
      if (this.currentUserId && userId && this.currentUserId !== userId) {
        this.resetChatState()
      }

      if (userId && !this.currentUserId) {
        this.currentUserId = userId
      }

      if (this.isLoaded && !force) return

      try {
        const chats = await fetchAllUserChats()
        this.userChats = [...chats]
          .sort((first, second) => {
            const firstUpdatedAt = new Date(first.updated_at).getTime()
            const secondUpdatedAt = new Date(second.updated_at).getTime()
            return secondUpdatedAt - firstUpdatedAt
          })
          .map((chat) => ({
          ...chat,
          messages: chat.messages || [],
        }))

        if (!this.activeChat && this.userChats.length > 0) {
          // Näytetään aina viimeisin olemassa oleva chat johdonmukaisesti kirjautumisen jälkeen
          const initialChatId = this.userChats[0].id
          await this.setActiveChat(initialChatId)
        }

        this.isLoaded = true
      } catch (error) {
        console.error("Käyttäjän chattien alustus epäonnistui:", error)
        throw error
      }
    },

    async setActiveChat(chatId) {
      if (this.activeChat?.id === chatId) return this.activeChat

      this.isLoadingChat = true

      try {
        const chat = await fetchChat(chatId)
        this.activeChat = {
          ...chat,
          messages: chat.messages || [],
        }
        this.upsertChatSummary(chat)
        return this.activeChat
      } catch (error) {
        console.error("Aktiivisen chatin lataus epäonnistui:", error)
        throw error
      } finally {
        this.isLoadingChat = false
      }
    },

    async createChat() {
      try {
        const newChat = await addChat()

        this.activeChat = {
          ...newChat,
          messages: newChat.messages || [],
        }
        this.upsertChatSummary(newChat)

        return this.activeChat
      } catch (error) {
        console.error("Uuden chatin luonti epäonnistui:", error)
        throw error
      }
    },

    async ensureWritableActiveChat() {
      if (!this.activeChat) {
        return this.createChat()
      }

      if (!LOCKED_STATUSES.includes(this.activeChat.status)) {
        return this.activeChat
      }

      const writableChat = this.getWritableChat
      if (writableChat) {
        return this.setActiveChat(writableChat.id)
      }

      return this.createChat()
    },

    async addUserMessage(message) {
      if (!this.activeChat) return
      if (this.isSending) return

      if (LOCKED_STATUSES.includes(this.activeChat.status)) {
        throw new Error("Chat on lukittu")
      }

      this.isSending = true

      // Näytetään käyttäjän viesti heti käyttöliittymässä ennen backend-vastausta
      const optimisticUserMessage = {
        id: crypto.randomUUID(),
        sender: "user",
        content: message,
        classification: "safe",
        flagged_for_human: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }

      this.activeChat.messages = [
        ...(this.activeChat.messages || []),
        optimisticUserMessage,
      ]

      try {
        const data = await sendUserMessage(this.activeChat.id, message)

        this.activeChat.messages = this.activeChat.messages.filter(
          (item) => item.id !== optimisticUserMessage.id,
        )
        this.activeChat.messages.push(data.userMessage)

        if (data.botMessage) {
          this.activeChat.messages.push(data.botMessage)
        }

        if (
          data.requires_professional ||
          data.userMessage.classification === "needs_review"
        ) {
          this.activeChat.status = "waiting_for_professional"
        }

        this.activeChat.updated_at =
          data.botMessage?.updated_at ||
          data.userMessage.updated_at ||
          this.activeChat.updated_at

        if (data.userMessage.classification === "emergency") {
          console.warn("Hätätilaviesti tunnistettu")
        }

        this.upsertChatSummary(this.activeChat)
      } catch (error) {
        console.error("Käyttäjän viestin lähetys epäonnistui:", error)
        this.activeChat.messages = this.activeChat.messages.filter(
          (item) => item.id !== optimisticUserMessage.id,
        )
        throw error
      } finally {
        this.isSending = false
      }
    },
  },
})
