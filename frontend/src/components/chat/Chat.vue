<template>
  <div class="chat-container">

    <div
      class="messages"
      :class="{ 'messages--welcome': welcomeMessageDisplayed }"
      ref="messagesEl"
    >
      <!-- Tervetuloa-näyttö -->
      <section v-if="welcomeMessageDisplayed" class="welcome">
        <div class="welcome-hero">
          <div class="welcome-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" class="welcome-icon-svg">
              <path
                d="M7 8h10M7 12h6M12 20l-3.5-3H7a4 4 0 0 1-4-4V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v6a4 4 0 0 1-4 4h-1.5L12 20z"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>

          <h2 class="welcome-title">
            {{ $t("welcomeTitle") }}
          </h2>
          <p class="welcome-subtitle">
            {{ $t("welcomeDescription") }}
          </p>
        </div>

        <div class="welcome-cards">
          <div class="welcome-card">
            <div class="card-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>

            <h3 class="card-title">
              {{ $t("chatbotHelpsTitle") }}
            </h3>
            <p class="card-text">
              {{ $t("chatbotHelpsDesc") }}
              <strong>{{ $t("chatbotHelpsDescBold") }}</strong>
            </p>
          </div>

          <div class="welcome-card">
            <div class="card-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </div>

            <h3 class="card-title">
              {{ $t("professionalSupportTitle") }}
            </h3>
            <p class="card-text">
              {{ $t("professionalSupportDesc") }}
            </p>
          </div>

          <div class="welcome-card">
            <div class="card-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </div>

            <h3 class="card-title">
              {{ $t("noDiagnosesTitle") }}
            </h3>
            <p class="card-text">
              {{ $t("noDiagnosesDesc") }}
            </p>
          </div>
        </div>

        <div
          class="welcome-alert"
          role="note"
          aria-label="Important information"
        >
          <div class="alert-icon" aria-hidden="true">!</div>
          <div class="alert-body">
            <div class="alert-title">
              {{ $t("importantInfo") }}
            </div>
            <ul class="alert-list">
              <li>{{ $t("importantInfo1") }}</li>
              <li>{{ $t("importantInfo2") }}</li>
              <li>{{ $t("importantInfo3") }}</li>
            </ul>
          </div>
        </div>
      </section>

      <ChatMessage
        v-for="message in messages"
        :key="message.id"
        :from="message.sender"
        :text="message.content"
        :guideline-excerpt="message.guideline_excerpt"
        :guideline-source="message.guideline_source"
        :guideline-source-url="message.guideline_source_url ?? null"
        :requires-confirmation="message.requires_confirmation ?? false"
        :requires-professional="message.requires_professional ?? false"
        :is-forward-confirmation="message.is_forward_confirmation ?? false"
        :is-emergency="message.classification === 'emergency'"
        :confirmation-answered="chatStore.pendingConfirmationMessageId !== message.id"
        :sources="message.sources || []"
        :extra-class="[
          message.classification === 'needs_review' && !message.requires_confirmation ? 'needs-review' : '',
          message.classification === 'emergency' ? 'emergency' : '',
        ]"
        @confirm-helpful="chatStore.dismissConfirmation()"
        @confirm-needs-forward="chatStore.forwardToProfessional()"
      />

      <!-- Bot typing indicator -->
      <div v-if="waitingForBot && !welcomeMessageDisplayed" class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
      </div>

      <!-- Waiting for professional reply -->
      <div v-if="waitingForProfessional" class="professional-waiting">
        <div class="sent-indicator">
          ✓ {{ $t("waitingProfessional.messageSent") }}
        </div>

        <div class="waiting-text">
          {{ $t("waitingProfessional.waiting") }}
        </div>

        <div class="response-time">
          {{ $t("waitingProfessional.responseTime") }}
        </div>
      </div>
    </div>

    <div v-if="authStore.isAuthenticated" class="input-shell">
      <div class="chat-input-wrapper">
        <ChatInputBar
          v-model="newMessage"
          :placeholder="$t('prompt')"
          :input-disabled="false"
          :send-disabled="waitingForBot"
          :show-edit="false"
          :is-editing="false"
          @send="handleSendFromInputBar"
        />
      </div>
      <div class="disclaimer">
        {{ $t('disclaimer') }}
      </div>
    </div>

    <div v-else class="input-shell auth-prompt-shell">
      <p class="auth-prompt-text">
        <a href="#" @click.prevent="triggerAuthModal('login')">
          {{ $t('settings.login') }}
        </a>
        {{ $t('or') }}
        <a href="#" @click.prevent="triggerAuthModal('register')">
          {{ $t('settings.register') }}
        </a>
        {{ $t('authPromptSuffix') }}
      </p>
    </div>
  </div>
</template>

<script>
import ChatMessage from "./ChatMessage.vue"
import ChatInputBar from "./ChatInputBar.vue"
import { useI18n } from "vue-i18n"
import { useUserChatStore } from "@/stores/userChatStore"
import { useAuthStore } from "@/stores/authStore"
import { onMounted, watch, ref, nextTick } from "vue"
import { chatSocket } from "@/services/chatSocket"

export default {
  name: "ChatComponent",
  components: { ChatMessage, ChatInputBar },

  props: {
    externalShowForm: Boolean,
  },

  emits: ["update:externalShowForm", "trigger-auth-modal"],

  setup(props, { emit }) {
        function triggerAuthModal(tab) {
          emit('trigger-auth-modal', tab)
        }
    const { t } = useI18n()
    const chatStore = useUserChatStore()
    const authStore = useAuthStore()

    const welcomeMessageDisplayed = ref(true)
    const messagesEl = ref(null)
    const newMessage = ref("")
    const waitingForBot = ref(false)
    const waitingForProfessional = ref(false)
    const showForm = ref(false)

    const syncWaitingIndicators = (chat) => {
      if (!authStore.isAuthenticated || !chat) {
        waitingForBot.value = false
        waitingForProfessional.value = false
        return
      }

      if (!["waiting_for_professional", "in_progress"].includes(chat.status)) {
        waitingForProfessional.value = false
      }
    }

    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesEl.value) {
          messagesEl.value.scrollTo({
            top: messagesEl.value.scrollHeight,
            behavior: "smooth",
          })
        }
      })
    }

    const connectWebsocket = (chat) => {
      if (!chat) return
      // Älä yhdistä websocketia draft-chateille
      if (chat.isDraft) return
      chatSocket.connect(chat.id, authStore.token, (data) => {
        if (data.sender !== authStore.getCurrentUserID) {
          chat.messages.push(data.message)

          if (data.chatStatus !== chat.status) {
            chatStore.updateChatStatus(data.chatStatus)
          }

          if (data.message?.sender === "professional") {
            waitingForProfessional.value = false
          }
          if (data.chatStatus === "closed") {
            waitingForProfessional.value = false
          }
          scrollToBottom()
        }
      })
    }

    onMounted(() => {
      chatStore.resetTransientState()
      syncWaitingIndicators(chatStore.activeChat)

      if (chatStore.activeChat) {
        connectWebsocket(chatStore.activeChat)
        welcomeMessageDisplayed.value = !chatStore.activeChat.messages?.length
        scrollToBottom()
      }
    })

    watch(
      () => chatStore.activeChat,
      (newChat) => {
        if (!newChat) {
          syncWaitingIndicators(null)
          welcomeMessageDisplayed.value = true
          return
        }
        syncWaitingIndicators(newChat)
        connectWebsocket(newChat)
        welcomeMessageDisplayed.value = !newChat.messages?.length
        scrollToBottom()
      },
      { immediate: true },
    )

    watch(
      () => chatStore.activeChat?.messages,
      (messages) => {
        welcomeMessageDisplayed.value = !messages?.length
        scrollToBottom()
      },
      { deep: true },
    )

    watch(
      () => chatStore.activeChat?.status,
      () => {
        syncWaitingIndicators(chatStore.activeChat)
      },
      { immediate: true },
    )

    watch(
      () => authStore.isAuthenticated,
      (isAuthenticated) => {
        if (!isAuthenticated) {
          syncWaitingIndicators(null)
        }
      },
      { immediate: true },
    )

    watch(
      () => props.externalShowForm,
      (val) => {
        showForm.value = val
      },
    )

    const handleSendFromInputBar = async (text) => {
      if (!authStore.isAuthenticated) return
      if (!text.trim()) return

      newMessage.value = ""

      try {
        const chat = chatStore.activeChat
        // Luo chat vain jos sitä ei ole, tai se on draft
        if (!chat || chat.isDraft) {
          if (!chat) {
            chatStore.createDraftChat()
          }
          // Jos chat on draft, se tallennetaan kun addUserMessage kutsutaan
        }

        if (chat?.status === "in_progress") {
          waitingForProfessional.value = true
        } else {
          waitingForBot.value = true
        }

        await chatStore.addUserMessage(text.trim())
      } catch (error) {
        console.error("Send error:", error)
      } finally {
        waitingForBot.value = false
        scrollToBottom()
      }
    }

    return {
      t,
      chatStore,
      authStore,
      welcomeMessageDisplayed,
      messagesEl,
      newMessage,
      waitingForBot,
      waitingForProfessional,
      showForm,
      scrollToBottom,
      handleSendFromInputBar,
      triggerAuthModal,
    }
  },

  computed: {
    messages() {
      return this.chatStore.getActiveChat?.messages ?? []
    },
  },
}
</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100%;
  min-height: 0;

  display: flex;
  flex-direction: column;

  padding: 24px 0 0;
  box-sizing: border-box;
}

.messages {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;

  max-width: 860px;
  width: 100%;
  margin: 0 auto;

  padding: 0 18px 18px;
  box-sizing: border-box;
}

.messages--welcome {
  overflow-y: auto;
}

.welcome,
.welcome * {
  font-family:
    ui-sans-serif,
    system-ui,
    -apple-system,
    "Segoe UI",
    Roboto,
    Arial,
    "Noto Sans",
    "Liberation Sans",
    sans-serif;
}

.welcome {
  max-width: 860px;
  margin: 0 auto;
  padding: 24px 0 1;
  font-size: 18px;
  line-height: 1;
}

.welcome-hero {
  text-align: center;
  padding-bottom: 18px;
}

.welcome-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 18px;
  border-radius: 18px;
  background: #1d4ed8;
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 16px 40px rgba(29, 78, 216, 0.25);
}

.welcome-icon-svg {
  width: 30px;
  height: 30px;
}

.welcome-title {
  font-size: 28px;
  line-height: 1.2;
  margin: 0 0 10px;
  color: #0f172a;
  font-weight: 750;
}

.welcome-subtitle {
  margin: 0 auto;
  max-width: 620px;
  color: #445164;
  font-size: 18px;
  line-height: 1.4;
}

.welcome-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 0px;
}

.welcome-card {
  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #dbeafe;
  display: grid;
  place-items: center;
  margin-bottom: 12px;
  color: #1264a3;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.card-title {
  margin: 0 0 8px;
  font-size: 18px;
  color: #0f172a;
}

.card-text {
  margin: 0;
  font-size: 18px;
  line-height: 1.55;
  color: #1d2e3e;
}

.welcome-alert {
  margin: 18px auto 0;
  background: #fff7ed;
  border: 1px solid #fde68a;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.alert-icon {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: #ffedd5;
  color: #92400e;
  display: grid;
  place-items: center;
  font-weight: 750;
  flex: 0 0 auto;
}

.alert-title {
  font-weight: 750;
  color: #7c2d12;
  font-size: 18px;
  margin-bottom: 8px;
}

.alert-list {
  margin: 0;
  padding-left: 18px;
  color: #7c2d12;
  font-size: 18px;
  line-height: 1.55;
}

.input-shell {
  width: 100%;
  padding: 16px 18px 24px;
  box-sizing: border-box;

  background: rgba(226, 240, 255, 0.92);
  backdrop-filter: blur(6px);
  border-top: 1px solid rgba(203, 213, 225, 0.7);
  
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-shell > .chat-input-wrapper {
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
}

.disclaimer {
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
  font-size: 12px;
  color: #5f6c7b;
  text-align: center;
  line-height: 0;
  padding: 8px 0 0;
}

.auth-prompt-shell {
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 20px 18px;
}

.auth-prompt-text {
  font-size: 18px;
  color: #1d2e3e;
  margin: 0;
  max-width: 600px;
  line-height: 1.6;
}

.auth-prompt-text a {
  color: #3a5bdc; /* Sama sininen kuin brändissänne */
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s ease;
}

.auth-prompt-text a:hover {
  color: #2a45b8;
  text-decoration: underline;
}

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 12px 16px;
  margin: 8px 0;
  width: fit-content;
  background: #f1f5f9;
  border-radius: 14px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #2d445a;
  border-radius: 50%;
  animation: typing 1.2s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

.professional-waiting {
  margin: 12px 0;
  padding: 12px 16px;
  background: #f1f5f9;
  border-radius: 12px;
  font-size: 14px;
}

.sent-indicator {
  color: #16a34a;
  font-weight: 600;
  margin-bottom: 4px;
}

.waiting-text {
  font-weight: 500;
}

.response-time {
  color: #2d445a;
  font-size: 13px;
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
