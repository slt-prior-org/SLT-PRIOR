import { defineStore } from "pinia"
import { addProfessionalMessage, close, claim, fetchQueues } from "@/services/professionalChatService"
import { useAuthStore } from "@/stores/authStore"

export const useProfessionalChatStore = defineStore("professionalChat", {
  state: () => ({
    queues: {
      in_progress: [],
      waiting: [],
      closed: []
    },
    isLoaded: false,
    activeChatId: null,
  }),

  getters: {
    getInProgressChats: (state) => state.queues.in_progress,
    getWaitingChats: (state) => state.queues.waiting,
    getClosedChats: (state) => state.queues.closed,

    getActiveChat(state) {
      const allChats = Object.values(state.queues).flat()
      return allChats.find(chat => chat.id === state.activeChatId) || null
    }
  },

  actions: {
    setActiveChat(chatId) {
      this.activeChatId = chatId
    },
    async initializeQueues() {
      if (this.isLoaded) return
      try {
        const queues = await fetchQueues()

        this.queues.waiting = queues.waiting || []
        this.queues.in_progress = queues.in_progress || []
        this.queues.closed = queues.closed || []

        this.isLoaded = true
      } catch (error) {
        console.error("Failed to load queues:", error)
      }
    },
    async claimChat() {
      const chat = this.getActiveChat
      if(!chat) return

      const authStore = useAuthStore()

      if(chat.assigned_professional_id) {
        console.log("Chat already assigned to another professional")
        return
      }

      if (chat.status !== "waiting") {
        console.log("Chat is not in waiting state")
        return
      }

      try {
        await claim(chat.id)

        chat.status = "in_progress"
        chat.assigned_professional_id = authStore.getCurrentUserID

        this.moveChatBetweenQueues(chat, "waiting", "in_progress")

      } catch(error) {
        console.error("Failed to claim the chat:", error)
      }
    },
    async closeChat() {
      const chat = this.getActiveChat
      if (!chat) return

      const authStore = useAuthStore()

      if (chat.status !== "in_progress") {
        console.log("Chat is not in progress")
        return
      }

      
      if (chat.assigned_professional_id !== authStore.getCurrentUserID) {
        console.log("You are not assigned to this chat")
        return
      }

      try {
        await close(chat.id)

        chat.status = "closed"

        this.moveChatBetweenQueues(chat, "in_progress", "closed")

      } catch (error) {
        console.error("Failed to close the chat:", error)
      }
    },
    moveChatBetweenQueues(chat, fromQueue, toQueue) {
      this.queues[fromQueue] = this.queues[fromQueue].filter(c => c.id !== chat.id)

      this.queues[toQueue].push(chat)
    },
    async sendProfessionalMessage(chatId, message) {
      const chat = this.getActiveChat
      if (!chat) return

      try {
        const savedMessage = await addProfessionalMessage(chatId, { message })

        if (!chat.messages) chat.messages = []
        chat.messages.push(savedMessage)

      } catch (error) {
        console.error("Failed to send professional message:", error)
      }
    }
  }
})
