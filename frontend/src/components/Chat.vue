<template>
  <div class="chat-container">
    <!-- Esitietolomake-modal -->
    <PatientForm v-if="showForm" @close="closePatientForm" />

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
              <span class="icon-dot" />
            </div>

            <h3 class="card-title">
              {{ $t("chatbotHelpsTitle") }}
            </h3>
            <p class="card-text"
              v-html= "$t('chatbotHelpsDesc')">
            </p>
          </div>

          <div class="welcome-card">
            <div class="card-icon" aria-hidden="true">
              <span class="icon-dot" />
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
              <span class="icon-dot" />
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
        :sources="message.sources || []"
        :extra-class="[
          message.classification === 'needs_review' ? 'needs-review' : '',
          message.classification === 'emergency' ? 'emergency' : '',
        ]"
      />

      <!-- Bot typing indicator -->
      <div v-if="waitingForBot" class="typing-indicator">
        <span></span>
        <span></span>
        <span></span>
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
    </div>

   <div v-else class="input-shell auth-prompt-shell">
      <p class="auth-prompt-text">
        <a href="#" @click.prevent="$emit('open-login')">
          {{ $t('settings.login') }}
        </a> 
        {{ $t('or') }} 
        <a href="#" @click.prevent="$emit('open-register')">
          {{ $t('settings.register') }}
        </a>
        {{ $t('authPromptSuffix') }}
      </p>
    </div>
  </div>  
</template>

<script>
import PatientForm from "./PatientForm.vue"
import ChatMessage from "./chat/ChatMessage.vue"
import ChatInputBar from "./chat/ChatInputBar.vue"
import { useI18n } from "vue-i18n"
import { useUserChatStore } from "@/stores/userChatStore"
import { useAuthStore } from "@/stores/authStore"
import { onMounted, watch, ref, nextTick } from "vue"
import { chatSocket } from "@/services/chatSocket"

export default {
  name: "ChatComponent",
  components: { PatientForm, ChatMessage, ChatInputBar },

  props: {
    externalShowForm: Boolean,
  },

  emits: ["update:externalShowForm", "open-login", "open-register"],

  setup(props, { emit }) {
    const { t } = useI18n()
    const chatStore = useUserChatStore()
    const authStore = useAuthStore()

    const welcomeMessageDisplayed = ref(true)
    const messagesEl = ref(null)
    const newMessage = ref("")
    const waitingForBot = ref(false)
    const showForm = ref(false)

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
      chatSocket.connect(chat.id, authStore.token, (message) => {
        chat.messages.push(message)
        chatStore.updateChatStatus("open")
        scrollToBottom()
      })
    }

    onMounted(() => {
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
          welcomeMessageDisplayed.value = true
          return
        }
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
      () => props.externalShowForm,
      (val) => {
        showForm.value = val
      },
    )

    const openPatientForm = () => {
      showForm.value = true
      emit("update:externalShowForm", true)
    }

    const closePatientForm = () => {
      showForm.value = false
      emit("update:externalShowForm", false)
    }

    const handleSendFromInputBar = async (text) => {
      if (!authStore.isAuthenticated) return
      if (!text.trim()) return

      newMessage.value = ""
      waitingForBot.value = true
      welcomeMessageDisplayed.value = false

      try {
        // Luo chat vain jos sitä ei ole
        if (!chatStore.activeChat) {
          await chatStore.createChat()
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
      showForm,
      scrollToBottom,
      handleSendFromInputBar,
      openPatientForm,
      closePatientForm,
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
  max-width: 640px;
  color: #475569;
  font-size: 18px;
  line-height: 1.6;
}

.welcome-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 0px;
}

.welcome-card {
  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
}

.card-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #eff6ff;
  display: grid;
  place-items: center;
  margin-bottom: 10px;
}

.icon-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: #2563eb;
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
  color: #475569;
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
  padding: 12px 18px 18px;
  box-sizing: border-box;

  background: rgba(226, 240, 255, 0.92);
  backdrop-filter: blur(6px);
  border-top: 1px solid rgba(203, 213, 225, 0.7);
}

.input-shell > .chat-input-wrapper {
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
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
  color: #475569;
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
  background: #64748b;
  border-radius: 50%;
  animation: typing 1.2s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
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
