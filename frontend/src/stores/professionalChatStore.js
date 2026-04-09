import { defineStore } from "pinia"
import {
  addProfessionalMessage,
  close,
  claim,
  fetchQueues,
  fetchChat,
  unclaim,
} from "@/services/professionalChatService"
import { useAuthStore } from "@/stores/authStore"
import { professionalQueueSocket } from "@/services/professionalQueueSocket"

export const useProfessionalChatStore = defineStore("professionalChat", {
  state: () => ({
    queues: {
      in_progress: [],
      waiting: [],
      closed: [],
    },
    loading: {
      queues: false,
      chat: false,
      claim: false,
      close: false,
      send: false,
    },
    activeChat: null,
    socket: null
  }),

  getters: {
    getInProgressChats: (state) => state.queues.in_progress,
    getWaitingChats: (state) => state.queues.waiting,
    getClosedChats: (state) => state.queues.closed,
    getMyInProgressChats: (state) => {
      return (userId) =>
        state.queues.in_progress.filter(
          (chat) => chat.assigned_professional_id === userId,
        )
    },
  },

  actions: {
    async initializeQueues() {
      if (this.loading.queues) return

      try {
        this.loading.queues = true
        const queues = await fetchQueues()

        this.queues.waiting = queues.waiting || []
        this.queues.in_progress = queues.in_progress || []
        this.queues.closed = queues.closed || []
      } catch (error) {
        console.error("Failed to load queues:", error)
      } finally {
        this.loading.queues = false
      }
    },
    async openChat(chatId) {
      if (this.loading.chat) return

      try {
        this.loading.chat = true

        const chat = await fetchChat(chatId)
        this.activeChat = chat
      } catch (error) {
        console.error("Failed to fetch chat:", error)
      } finally {
        this.loading.chat = false
      }
    },
    clearActiveChat() {
      this.activeChat = null
    },
    async claimChat(chatId) {
      if (this.loading.claim) return

      const authStore = useAuthStore()

      const chat = this.queues.waiting.find((c) => c.id === chatId)
      if (!chat) return

      if (
        chat.assigned_professional_id !== authStore.getCurrentUserID &&
        chat.assigned_professional_id !== null
      ) {
        console.log("Chat already assigned to another professional")
        console.log(
          "Chat assigned professional ID:",
          chat.assigned_professional_id,
        )
        console.log("Current user ID:", authStore.getCurrentUserID)
        return
      }

      try {
        this.loading.claim = true

        await claim(chatId)

        chat.status = "in_progress"
        chat.assigned_professional_id = authStore.getCurrentUserID

        this.moveChatBetweenQueues(chat, "waiting", "in_progress")

        if (this.activeChat?.id === chatId) {
          this.activeChat.status = "in_progress"
          this.activeChat.assigned_professional_id = authStore.getCurrentUserID
        }
      } catch (error) {
        console.error("Failed to claim the chat:", error)
      } finally {
        this.loading.claim = false
      }
    },
    async unclaimChat(chatId) {
      if (this.loading.claim) return

      const authStore = useAuthStore()

      const chat = this.queues.in_progress.find((c) => c.id === chatId)
      if (!chat) return

      if (chat.assigned_professional_id !== authStore.getCurrentUserID) {
        console.log("You are not assigned to this chat")
        return
      }

      try {
        this.loading.claim = true

        await unclaim(chatId)

        chat.status = "waiting_for_professional"
        chat.assigned_professional_id = null

        this.moveChatBetweenQueues(chat, "in_progress", "waiting")

        if (this.activeChat?.id === chatId) {
          this.activeChat.status = "waiting_for_professional"
          this.activeChat.assigned_professional_id = null
        }
      } catch (error) {
        console.error("Failed to unclaim the chat:", error)
      } finally {
        this.loading.claim = false
      }
    },
    async closeChat(chatId) {
      console.log("Attempting to close chat with ID:", chatId)
      if (this.loading.close) return

      const authStore = useAuthStore()

      const chat = this.queues.in_progress.find((c) => c.id === chatId)
      console.log("Found chat in in_progress queue:", chat)
      if (!chat) return

      if (chat.status !== "in_progress") {
        console.log("Chat is not in progress")
        return
      }

      if (chat.assigned_professional_id !== authStore.getCurrentUserID) {
        console.log("You are not assigned to this chat")
        return
      }

      try {
        this.loading.close = true

        await close(chatId)
        console.log("Chat closed successfully")

        chat.status = "closed"

        this.moveChatBetweenQueues(chat, "in_progress", "closed")

        if (this.activeChat?.id === chatId) {
          this.activeChat.status = "closed"
        }
      } catch (error) {
        console.error("Failed to close the chat:", error)
      } finally {
        this.loading.close = false
      }
    },
    moveChatBetweenQueues(chat, fromQueue, toQueue) {
      this.queues[fromQueue] = this.queues[fromQueue].filter(
        (c) => c.id !== chat.id,
      )

      if (!this.queues[toQueue].some((c) => c.id === chat.id)) {
        this.queues[toQueue].push(chat)
      }
    },
    async sendProfessionalMessage(message) {
      if (this.loading.send) return

      const chat = this.activeChat
      if (!chat) return

      try {
        this.loading.send = true

        const savedMessage = await addProfessionalMessage(chat.id, { message })

        if (!chat.messages) chat.messages = []
        chat.messages.push(savedMessage)
      } catch (error) {
        console.error("Failed to send professional message:", error)
      } finally {
        this.loading.send = false
      }
    },

    // Connect to professionalQueueSocket
    async connectToQueueSocket(){
      professionalQueueSocket.connect(() => {
        // Update the professional queue
        this.initializeQueues()
      })
    },
    
    // End the websocket connection
    async disconnectFromQueueSocket(){
      professionalQueueSocket.disconnect()
    },
  },
})