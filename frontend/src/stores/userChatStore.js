// Pinia-tietovarasto chatille ja viestien hallinnalle
import { defineStore } from "pinia"
import {
  addChat,
  fetchAllUserChats,
  sendUserMessage,
  fetchChat,
  updateChatStatus,
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
      this.isSending = false
      this.isLoadingChat = false
      this.pendingConfirmationMessageId = null
      if (sessionStorage.getItem("userChat")) {
        sessionStorage.removeItem("userChat")
      }
    },
    resetTransientState() {
      this.isSending = false
      this.isLoadingChat = false
      this.pendingConfirmationMessageId = null
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
      if (!chatId || (this.activeChat && this.activeChat.id === chatId)) return

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
    // Luodaan paikallinen draft-chat ilman backend-tallennusta
    createDraftChat() {
      const draftChat = {
        id: crypto.randomUUID(),
        status: "draft",
        messages: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        isDraft: true,
      }

      this.activeChat = draftChat

      return draftChat
    },
    // Luodaan chat backendissä
    async createChat() {
      try {
        const newChat = await addChat()

        this.userChats.unshift({
          id: newChat.id,
          status: newChat.status,
          title: newChat.title ?? null,
          created_at: newChat.created_at,
          updated_at: newChat.updated_at,
        })

        await this.setActiveChat(newChat.id)

        return this.activeChat
      } catch (error) {
        console.error("Failed to create chat:", error)
        throw error
      }
    },
    // Tallennetaan draft-chat backendiin
    async saveDraftChat() {
      if (!this.activeChat || !this.activeChat.isDraft) return

      try {
        const newChat = await addChat()

        this.activeChat = {
          ...newChat,
          messages: [],
        }

        this.userChats.unshift({
          id: newChat.id,
          status: newChat.status,
          title: newChat.title ?? null,
          created_at: newChat.created_at,
          updated_at: newChat.updated_at,
        })

        return this.activeChat
      } catch (error) {
        console.error("Failed to save draft chat:", error)
        throw error
      }
    },
    updateChatStatus(status) {
      // Päivitetään aktiivisen chatin status
      this.activeChat.status = status

      // Päivitetään myös userChats-taulukossa oleva chat
      const index = this.userChats.findIndex((c) => c.id === this.activeChat.id)
      if (index !== -1) {
        this.userChats[index].status = status
      }
    },
    // Viestin lähetys chatissa (vain tila ja API, ei UI)
    async addUserMessage(message) {
      if (!this.activeChat) return

      if (this.isSending) return // Estää useat lähetykset

      if (
        ["waiting_for_professional"].includes(
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

      let chat = this.activeChat

      // Tallenna draft-chat backendiin ennen ensimmäisen viestin lähettämistä
      if (chat.isDraft) {
        try {
          await this.saveDraftChat()
          // Päivitä chat-viittaus saveDraftChatista, jossa ID muuttuu
          chat = this.activeChat
        } catch (error) {
          this.isSending = false
          throw error
        }
      }

      // Seurataan onko kyseessä ensimmäinen viesti (title-päivitystä varten)
      const wasFirstMessage = chat.messages.length === 0

      // Näytetään käyttäjän viesti heti käyttöliittymässä ennen backend-vastausta
      const userMessage = {
        id: crypto.randomUUID(),
        sender: "user",
        content: message,
        classification: "safe",
        flagged_for_human: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }


      chat.messages.push(userMessage)
      // Päivitä userChats-listan messages myös
      const chatIndex = this.userChats.findIndex(c => c.id === chat.id)
      if (chatIndex !== -1) {
        if (!this.userChats[chatIndex].messages) this.userChats[chatIndex].messages = []
        this.userChats[chatIndex].messages.push(userMessage)
      }

      try {
        const data = await sendUserMessage(chat.id, message)

        const confirmedUserMessage = data.userMessage ?? {
          id: userMessage.id,
          sender: "user",
          content: message,
          classification: "safe",
          flagged_for_human: false,
          created_at: userMessage.created_at,
          updated_at: userMessage.updated_at,
        }

        const botMessage = data.botMessage
          ? {
              ...data.botMessage,
              requires_confirmation: data.requires_confirmation ?? false,
              requires_professional: data.requires_professional ?? false,
              guideline_excerpt: data.guideline_excerpt ?? null,
              guideline_source: data.guideline_source ?? null,
              guideline_source_url: data.guideline_source_url ?? null,
            }
          : data.reply
            ? {
                id: crypto.randomUUID(),
                sender: "bot",
                content: data.reply ?? "",
                classification: data.classification ?? "safe",
                flagged_for_human: false,
                sources: data.sources ?? [],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              }
            : null


        chat.messages = chat.messages.filter(
          (item) => item.id !== userMessage.id,
        )
        chat.messages.push(confirmedUserMessage)
        // Päivitä userChats-listan messages myös
        if (chatIndex !== -1) {
          this.userChats[chatIndex].messages = chat.messages.slice()
        }

        if (botMessage) {
          chat.messages.push(botMessage)
          // Päivitä userChats-listan messages myös
          if (chatIndex !== -1) {
            this.userChats[chatIndex].messages = chat.messages.slice()
          }
        }

        if (
          (data.requires_professional || confirmedUserMessage.classification === "needs_review")
          && !data.requires_confirmation
        ) {
          this.updateChatStatus("waiting_for_professional")
        }

        if (confirmedUserMessage.classification === "emergency") {
          console.warn("Hätätilaviesti tunnistettu")
        }

        if (data.requires_confirmation && botMessage) {
          this.pendingConfirmationMessageId = botMessage.id
        }

        chat.updated_at =
          botMessage?.updated_at ||
          confirmedUserMessage.updated_at ||
          chat.updated_at
        
        // Päivitä userChats-listan updated_at myös
        if (chatIndex !== -1) {
          this.userChats[chatIndex].updated_at = chat.updated_at
        }
      } catch (error) {
        console.error("Käyttäjän viestin lähetys epäonnistui:", error)
        chat.messages = chat.messages.filter(
          (item) => item.id !== userMessage.id,
        )
        throw error
      } finally {
        this.isSending = false
      }

      // Haetaan AI-generoitu title ensimmäisen viestin jälkeen viiveellä
      if (wasFirstMessage) {
        const chatIdForRefresh = chat.id
        setTimeout(async () => {
          try {
            const updated = await fetchChat(chatIdForRefresh)
            if (updated.title) {
              const idx = this.userChats.findIndex(c => c.id === chatIdForRefresh)
              if (idx !== -1) {
                this.userChats[idx] = { ...this.userChats[idx], title: updated.title }
              }
              if (this.activeChat?.id === chatIdForRefresh) {
                this.activeChat = { ...this.activeChat, title: updated.title }
              }
            }
          } catch (e) { /* ignore */ }
        }, 5000)
      }
    },

    async forwardToProfessional() {
      if (!this.activeChat) return
      const forwardMsg = {
        id: crypto.randomUUID(),
        sender: "bot",
        content: "",
        flagged_for_human: false,
        classification: "needs_review",
        requires_confirmation: false,
        is_forward_confirmation: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      this.activeChat.messages.push(forwardMsg)
      this.activeChat.status = "waiting_for_professional"
      this.pendingConfirmationMessageId = null
      await updateChatStatus(this.activeChat.id, "waiting_for_professional")
    },

    dismissConfirmation() {
      this.pendingConfirmationMessageId = null
    },
    async loadChatsWithMessages() {
      if (this.userChats.length === 0) return

      try {
        // Hae data kaikille chateille
        const fullChats = await Promise.all(
          this.userChats.map(chat => fetchChat(chat.id))
        )
        
        // Korvaa userChats full-datalla
        this.userChats = fullChats
      } catch (error) {
        console.error('Chatien full-datan lataaminen epäonnistui:', error)
        throw error
      }
    },
  },
  persist: {
    storage: sessionStorage,
    key: "userChat",
    paths: ["userChats", "activeChat"], // vain nämä osiot tallennetaan
  },
})
