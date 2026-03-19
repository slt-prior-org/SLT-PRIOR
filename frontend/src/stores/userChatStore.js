import { defineStore } from "pinia"
import { addChat, fetchAllUserChats, sendUserMessage } from "@/services/userChatService"

export const useUserChatStore = defineStore("userChat", {
  state: () => ({
    userChats: [],
    activeChatId: null,
    isLoaded: false
  }),

  getters: {
    getUserChats: (state) => state.userChats,

    getActiveChat(state) {
      if (!state.activeChatId) return null
      return state.userChats.find(chat => chat.id === state.activeChatId) || null
    }
  },

  actions: {
    setActiveChat(chatId) {
      this.activeChatId = chatId
    },

    async initializeChats() {
      if (this.isLoaded) return
      try {
        const chats = await fetchAllUserChats()
        this.userChats = chats

        this.isLoaded = true
      } catch (error) {
        console.error("Failed to initialize user chats:", error)
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

        const userMessage = data.userMessage ?? {
          sender: "user",
          content: message,
          classification: "safe",
          sources: []
        }

        const botMessage = data.botMessage ?? {
          sender: "bot",
          content: data.reply ?? "",
          classification: data.classification ?? "safe",
          sources: data.sources ?? []
        }

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
