<template>
  <div class="chat-container">
    <!-- Esitietolomake-modal -->
    <PatientForm 
      v-if="showForm" 
      @close="closePatientForm" 
    />

    <div class="messages">
      <!-- Tervetuloviesti, joka näytetään vain kerran ensimmäisenä viestinä -->
      <div
        v-if="welcomeMessageDisplayed"
        class="message other"
      >
        <div class="message-content">
          {{ $t("welcomeMessage") }}
          <a
            href="#"
            @click.prevent="openPatientForm"
          >{{ $t("fillForm") }}</a>.
          {{ $t("returnLater") }}
        </div>
      </div>

      <!-- Käyttäjän ja botin viestit -->
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="[
          'message',
          message.from === 'self' ? 'self' : 'other',
          message.from !== 'self' && message.classification === 'NEEDS_REVIEW' ? 'needs-review' : '',
          message.from !== 'self' && message.classification === 'EMERGENCY' ? 'emergency' : ''
        ]"
      >
        <div
          class="message-content"
          v-html="message.text"
        />
      </div>
    </div>

    <form
      class="input-area"
      @submit.prevent="sendMessage"
    >
      <input
        v-model="newMessage"
        type="text"
        :placeholder="$t('prompt')"
        required
      >
      <button type="submit">
        <p>{{ $t("send") }}</p>
      </button>
    </form>
  </div>
</template>

<script>
import PatientForm from "./PatientForm.vue";
import { api } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import { useUserChatStore } from "@/stores/userChatStore";
import { useI18n } from "vue-i18n"; // Lisätty kielituki

export default {
  name: "ChatComponent",
  components: {
    PatientForm,
  },
  props: {
    externalShowForm: Boolean,
  },
  setup() {
    const { t, locale } = useI18n(); // Hae kielituki
    const authStore = useAuthStore();
    const chatStore = useUserChatStore();
    return { t, locale, authStore, chatStore };
  },
  data() {
    return {
      userId: "user123",
      newMessage: "",
      showForm: false,
      isInitializing: false,
    };
  },
  computed: {
    activeChat() {
      return this.chatStore.getActiveChat;
    },
    messages() {
      return (this.activeChat?.messages || []).map(this.mapBackendMessage);
    },
    welcomeMessageDisplayed() {
      return this.messages.length === 0;
    },
  },
  watch: {
    externalShowForm(newVal) {
      this.showForm = newVal;
    },
  },
  async mounted() {
    await this.initializeActiveChat();
  },
  methods: {
    openPatientForm() {
      this.showForm = true;
      this.$emit("update:externalShowForm", true);
    },
    closePatientForm() {
      this.showForm = false;
      this.$emit("update:externalShowForm", false);
    },
    async fetchMapping() {
      try {
        const response = await api.get("/api/data"); // Ei löydy backendistä
        this.mapping = response.data.data;
      } catch (error) {
        console.error(this.$t("data-error"), error);
      }
    },
    normalizeClassification(classification) {
      if (!classification) return "SAFE";
      return String(classification).toUpperCase();
    },
    mapBackendMessage(message) {
      return {
        text: message.content,
        from: message.sender === "user" ? "self" : "other",
        classification: this.normalizeClassification(message.classification),
      };
    },
    async initializeActiveChat() {
      // Käytetään kirjautuneen käyttäjän omaa aktiivista chatia
      if (!localStorage.getItem("token")) {
        this.chatStore.resetChatState();
        return;
      }

      this.isInitializing = true;

      try {
        await this.chatStore.initializeChats(this.authStore.getCurrentUserID);

        if (!this.chatStore.getActiveChat) {
          await this.chatStore.createChat();
        }
      } catch (error) {
        console.error("Chatin alustus epäonnistui:", error);
      } finally {
        this.isInitializing = false;
      }
    },
    async sendMessage() {
      if (this.newMessage.trim() === "" || this.isInitializing) return;

      // Varmistetaan, että aktiivinen chat on olemassa ennen lähetystä
      if (!this.chatStore.getActiveChat) {
        await this.initializeActiveChat();
      }

      if (!this.chatStore.getActiveChat) {
        return;
      }

      try {
        await this.chatStore.addUserMessage(this.newMessage);
      } catch (error) {
        console.error(this.$t("send-error"), error);
      }

      // Tyhjennä syötekenttä
      this.newMessage = "";
    },
  },
};
</script>

<style scoped>
body {
  background-color: #f0f4f8;
  font-family: "Arial", sans-serif;
  margin: 0;
  padding: 0;
}

.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  flex-direction: column;
}

.logo {
  width: 200px;
  height: auto;
  max-width: 100%;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 123, 255, 0.2);
}

.chat-container {
  width: 100%;
  max-width: 600px;
  margin: 20px auto;
  background: #ffffff;
  border: 2px solid #005b96;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 91, 150, 0.2);
  display: flex;
  flex-direction: column;
  height: 80vh;
  box-sizing: border-box;
  padding: 20px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 15px;
  padding-right: 10px;
}

.message {
  margin-bottom: 10px;
  word-wrap: break-word;
}

.message.self {
  text-align: right;
}

.message.other {
  text-align: left;
}

.message-content {
  display: inline-block;
  padding: 10px 15px;
  border-radius: 20px;
  max-width: 75%;
  font-size: 1rem;
}

.message.self .message-content {
  background: #43a352;
  color: white;
}

.message.other .message-content {
  background: #e0e0e0;
  color: #333;
}

.message.needs-review .message-content {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffc107;
}

.message.emergency .message-content {
  background: #f8d7da;
  color: #721c24;
  border: 2px solid #dc3545;
  font-weight: bold;
}

.input-area {
  display: flex;
  align-items: center;
}

.input-area input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 20px;
  box-sizing: border-box;
  font-size: 1rem;
}

.input-area button {
  margin-left: 10px;
  padding: 10px 20px;
  border: none;
  border-radius: 20px;
  background-color: #005b96;
  color: white;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.input-area button:hover {
  background-color: #004080;
}

@media (max-width: 600px) {
  .logo {
    width: 150px;
  }

  .chat-container {
    height: 90vh;
    padding: 15px;
  }

  .message-content {
    font-size: 0.9rem;
  }

  .input-area input {
    padding: 8px;
  }

  .input-area button {
    padding: 8px 15px;
  }
}
</style>
