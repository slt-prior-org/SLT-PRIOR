// Pinia-tietovarasto chatille ja viestien hallinnalle
import { defineStore } from "pinia"
import {
  addChat,
  fetchAllUserChats,
  sendUserMessage,
  fetchChat,
} from "@/services/userChatService"

export const useUserChatStore = defineStore("userChat", {
  state: () => ({
    userChats: [], // Kaikki käyttäjän chatit
    activeChat: null, // Aktiivinen chat
    isLoaded: false, // Onko chatit ladattu
    isSending: false, // Estää viestien spam/race condition
    isLoadingChat: false,
    pendingConfirmationMessageId: null, // Seuraa odottavaa Kyllä/Ei-vahvistusta
  }),

  getters: {
    getUserChats: (state) => state.userChats, // Palauttaa kaikki chatit
    getActiveChat: (state) => state.activeChat,
  },

  actions: {
    clearChats() {
      this.userChats = [] // Tyhjentää chatit
      this.activeChat = null // Tyhjentää aktiivisen chatin
      this.isLoaded = false // Resetoi lataustilan
    },

    // Chatien haku ja alustaminen
    async initializeChats(force = false) {
      if (this.isLoaded && !force) return

      try {
        const chats = await fetchAllUserChats()

        this.userChats = chats

        // Aseta ensimmäinen chat aktiiviseksi jos ei ole
        //if (!this.activeChatId && this.userChats.length > 0) {
        //  this.activeChatId = this.userChats[0].id
        //}

        this.isLoaded = true
      } catch (error) {
        console.error("Failed to initialize user chats:", error)
        throw error
      }
    },
    // Aseta aktiivinen chat
    async setActiveChat(chatId) {
      if (this.activeChat?.id === chatId) return

      this.isLoadingChat = true

      try {
        const chat = await fetchChat(chatId)

        this.activeChat = {
          ...chat,
          messages: chat.messages || [],
        }
      } catch (error) {
        console.error("Failed to load chat:", error)
        throw error
      } finally {
        this.isLoadingChat = false
      }
    },
    // Uuden chatin luonti
    async createChat() {
      try {
        const newChat = await addChat()

        this.userChats.unshift({
          id: newChat.id,
          status: newChat.status,
          created_at: newChat.created_at,
          updated_at: newChat.updated_at,
        })

        this.activeChat = {
          ...newChat,
          messages: newChat.messages || [],
        }

        return this.activeChat
      } catch (error) {
        console.error("Failed to create chat:", error)
        throw error
      }
    },

    // Viestin lähetys chatissa (vain tila ja API, ei UI)
    async addUserMessage(message) {
      if (!this.activeChat) return

      if (this.isSending) return // Estää useat lähetykset

      if (
        ["waiting_for_professional", "in_progress"].includes(
          this.activeChat.status,
        )
      ) {
        throw new Error("Chat is locked") // Estää viestit tietyissä tiloissa
      }

      // Käyttäjä jatkoi kirjoittamista → unohdetaan odottava vahvistus
      if (this.pendingConfirmationMessageId) {
        this.pendingConfirmationMessageId = null
      }

      this.isSending = true

      const chat = this.activeChat

      // Lisätään käyttäjän viesti
      const userMessage = {
        id: crypto.randomUUID(),
        sender: "user",
        content: message,
        classification: undefined,
        flagged_for_human: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      console.log("User message:", userMessage)

      chat.messages.push(userMessage)

      try {
        const data = await sendUserMessage(chat.id, message)
        userMessage.classification = data.classification

        // Lisätään botin vastaus
        if (data.reply) {
          const botMessage = {
            id: crypto.randomUUID(),
            sender: "bot",
            content: data.reply,
            flagged_for_human: false,
            classification: data.classification,
            requires_confirmation: data.requires_confirmation ?? false,
            guideline_excerpt: data.guideline_excerpt ?? null,
            guideline_source: data.guideline_source ?? null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
          console.log("Bot message:", botMessage)

          chat.messages.push(botMessage)

          // Lukitus VAIN kun requires_professional = true (ei confirmation-tilassa)
          if (data.requires_professional && !data.requires_confirmation) {
            chat.status = "waiting_for_professional"
          }

          // Jos requires_confirmation, tallennetaan odottava viesti-id
          if (data.requires_confirmation) {
            this.pendingConfirmationMessageId = botMessage.id
          }
        }

        if (data.classification === "emergency") {
          console.warn("Emergency message detected")
        }
      } catch (error) {
        console.error("Failed to send user message:", error)
        chat.messages = chat.messages.filter((m) => m !== userMessage)
        throw error
      } finally {
        this.isSending = false
      }
    },

    forwardToProfessional() {
      if (!this.activeChat) return
      const forwardMsg = {
        id: crypto.randomUUID(),
        sender: "bot",
        content:
          "Ymmärretty. Keskustelusi on välitetty ammattilaiselle arvioitavaksi.<br><br>Understood. Your conversation has been forwarded to a professional.",
        flagged_for_human: false,
        classification: "needs_review",
        requires_confirmation: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      this.activeChat.messages.push(forwardMsg)
      this.activeChat.status = "waiting_for_professional"
      this.pendingConfirmationMessageId = null
    },

    dismissConfirmation() {
      this.pendingConfirmationMessageId = null
    },
  },
})
