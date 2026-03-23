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
            <p class="card-text">
              {{ $t("chatbotHelpsDesc") }}
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
        :extra-class="[
          message.classification === 'needs_review' ? 'needs-review' : '',
          message.classification === 'emergency' ? 'emergency' : '',
        ]"
      />
    </div>

    <div class="input-shell">
      <div class="chat-input-wrapper">
        <ChatInputBar
          v-model="newMessage"
          :placeholder="$t('prompt')"
          :input-disabled="!authStore.isAuthenticated"
          :send-disabled="waitingForBot || !authStore.isAuthenticated"
          :show-edit="false"
          :is-editing="false"
          @send="handleSendFromInputBar"
        />
      </div>
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

export default {
  name: "ChatComponent",
  components: { PatientForm, ChatMessage, ChatInputBar },

  props: {
    externalShowForm: Boolean,
  },

  emits: ["update:externalShowForm"],

  setup() {
    const { t } = useI18n()
    const chatStore = useUserChatStore()
    const authStore = useAuthStore()

    return { t, chatStore, authStore }
  },

  data() {
    return {
      newMessage: "",
      showForm: false,
      welcomeMessageDisplayed: true,
      waitingForBot: false,
    }
  },

  computed: {
    messages() {
      return this.chatStore.getActiveChat?.messages ?? []
    },
  },

  watch: {
    externalShowForm(val) {
      this.showForm = val
    },

    messages: {
      handler(newMessages) {
        this.welcomeMessageDisplayed = newMessages.length === 0
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      },
      deep: true,
      immediate: false,
    },

    "chatStore.activeChat": {
      handler(activeChat) {
        console.log("Aktiivinen chat päivittyi, päivitä chat näkymä")
        if (!activeChat) {
          // Ei aktiivista chattiä -> tervetuloa näkyviin
          this.welcomeMessageDisplayed = true
          return
        }

        // Jos chatti on olemassa mutta viestejä ei ole -> tervetuloa
        this.welcomeMessageDisplayed = !activeChat.messages?.length
      },
      immediate: true,
      deep: true,
    },
  },

  methods: {
    openPatientForm() {
      this.showForm = true
      this.$emit("update:externalShowForm", true)
    },

    closePatientForm() {
      this.showForm = false
      this.$emit("update:externalShowForm", false)
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.messagesEl
        if (!el) return

        el.scrollTo({
          top: el.scrollHeight,
          behavior: "smooth",
        })
      })
    },

    handleSendFromInputBar(text) {
      if (!this.authStore.isAuthenticated) {
        console.warn("Käyttäjää ei ole tunnistettu")
        return
      }

      this.newMessage = ""
      this.sendMessage(text)
    },

    async sendMessage(text) {
      const outgoing = (text ?? "").trim()
      if (!outgoing) return
      if (this.waitingForBot) return
      if (!this.chatStore.getActiveChat) return

      this.waitingForBot = true
      this.welcomeMessageDisplayed = false

      try {
        await this.chatStore.addUserMessage(outgoing)
      } catch (error) {
        console.error(this.$t("send-error"), error)
      } finally {
        this.waitingForBot = false
      }
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

  max-width: 820px;
  width: 100%;
  margin: 0 auto;

  padding: 0 18px 18px;
  box-sizing: border-box;
}

.messages--welcome {
  overflow-y: hidden;
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
  max-width: 780px;
  margin: 0 auto;
  padding: 24px 0 12px;
  font-size: 18px;
  line-height: 1;
}

.welcome-hero {
  text-align: center;
  padding: 10px 10px 18px;
}

.welcome-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 18px;
  border-radius: 18px;
  background: #1d4ed8;
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 16px 40px rgba(29, 78, 216, 0.25);
}

.welcome-icon-svg {
  width: 40px;
  height: 40px;
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 10px;
}

.welcome-card {
  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
  min-height: 150px;
  padding-bottom: 10px;
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
  max-width: 820px;
  width: 100%;
  margin: 0 auto;
}
</style>
