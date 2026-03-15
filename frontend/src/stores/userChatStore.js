import { defineStore } from "pinia"
import { addChat, fetchAllUserChats, fetchChat, sendUserMessage } from "@/services/userChatService"

export const useUserChatStore = defineStore("userChat", {
  state: () => ({
    userChats: [],
    activeChatId: null,
    isLoaded: false,
    currentUserId: null
  }),

  getters: {
    getUserChats: (state) => state.userChats,

    getWritableChat(state) {
      return state.userChats.find(
        (chat) => !["waiting_for_professional", "in_progress"].includes(chat.status)
      ) || null
    },

    getActiveChat(state) {
      if (!state.activeChatId) return null
      return state.userChats.find(chat => chat.id === state.activeChatId) || null
    }
  },

  actions: {
    resetChatState() {
      // Tyhjennetään chat-tila, kun käyttäjä vaihtuu
      this.userChats = []
      this.activeChatId = null
      this.isLoaded = false
      this.currentUserId = null
    },

    setActiveChat(chatId) {
      this.activeChatId = chatId
    },

    async initializeChats(userId = null) {
      // Nollataan vanhan käyttäjän chatit, jos tunnistautunut käyttäjä vaihtui
      if (this.currentUserId && userId && this.currentUserId !== userId) {
        this.resetChatState()
      }

      if (userId && !this.currentUserId) {
        this.currentUserId = userId
      }

      if (this.isLoaded) return
      try {
        const chats = await fetchAllUserChats()
        this.userChats = chats.map((chat) => ({
          ...chat,
          messages: chat.messages || []
        }))

        // Valitaan ensisijaisesti kirjoitettavissa oleva chat
        if (!this.activeChatId && this.userChats.length > 0) {
          const writableChat = this.getWritableChat
          this.activeChatId = writableChat ? writableChat.id : this.userChats[0].id
          await this.loadActiveChat()
        }

        this.isLoaded = true
      } catch (error) {
        console.error("Failed to initialize user chats:", error)
      }
    },

    async loadActiveChat() {
      if (!this.activeChatId) return null

      try {
        const chat = await fetchChat(this.activeChatId)
        const existingIndex = this.userChats.findIndex((item) => item.id === chat.id)

        if (existingIndex >= 0) {
          this.userChats[existingIndex] = chat
        } else {
          this.userChats.push(chat)
        }

        return chat
      } catch (error) {
        console.error("Failed to load active chat:", error)
        throw error
      }
    },

    async createChat() {
      try {
        const newChat = await addChat()

        this.userChats.push({
          ...newChat,
          messages: []
        })

        this.activeChatId = newChat.id
        await this.loadActiveChat()

        return newChat
      } catch (error) {
        console.error("Failed to create chat:", error)
        throw error
      }
    },

    async addUserMessage(message) {
      const chat = this.getActiveChat
      if (!chat) return

      if (["waiting_for_professional", "in_progress"].includes(chat.status)) {
        return
      }

      try {
        const data = await sendUserMessage(chat.id, { message })

        const { userMessage, botMessage } = data

        chat.messages.push(userMessage)
        if (botMessage) chat.messages.push(botMessage)

        if (userMessage.classification === "needs_review") {
          chat.status = "waiting_for_professional"
        }

        if (userMessage.classification === "emergency") {
          console.log("Emergency message detected")
        }

      } catch (error) {
        console.error("Failed to send user message:", error)
      }
    },
  },
})
