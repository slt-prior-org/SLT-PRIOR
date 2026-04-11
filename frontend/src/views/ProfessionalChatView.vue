<template>
  <div class="page">
    <HeaderBar
      :queueCount="waiting.length"
      :closedCount="closedToday.length"
      :user="currentUser"
      :showLanguageSwitcher="true"
      :showCounts="true"
    />

    <div v-if="chatStore.loading.chat">Loading...</div>

    <div v-else class="chat-container">
      <div class="top-bar">
        <AppButton variant="neutral" @click="goBack">
          {{ $t("professional.back") }}
        </AppButton>
      </div>

      <div class="layout">

        <!-- CHAT -->
        <div class="conversation-card">

          <div 
            v-if="chat && chat.messages" 
            class="chat-messages"
            ref="messagesContainer"
            >
            <ChatMessage
              v-for="(msg, index) in visibleMessages"
              :key="messageKey(msg, index)"
              :from="msg.sender"
              :showLabel="true"
              :side="msg.sender === 'user' ? 'left' : 'right'"
              :senderType="msg.sender === 'user' ? 'customer' : msg.sender"
              :text="msg.content"
              :guideline-excerpt="msg.guideline_excerpt ?? null"
              :guideline-source="msg.guideline_source ?? null"
              :guideline-source-url="msg.guideline_source_url ?? null"
              :sources="msg.sources || []"
            />
          </div>

          <div v-if="!isClosed" class="divider"></div>

          <div v-if="!isClosed" class="reply-header">
            <div class="reply-label">
              {{ $t("professional.aiReply") }}
            </div>

            <AppButton
              variant="neutral"
              size="sm"
              @click="showSources = !showSources"
            >
              {{ showSources ? $t('professional.hideSources') : $t('professional.showSources') }}
            </AppButton>
          </div>

          <div v-if="showSources && !isClosed" class="sources-panel">
            <div class="sources-title">
              {{ $t("professional.sources") }}
            </div>

            <ul class="sources-list">
              <li v-for="(source, i) in suggestedReplySources" :key="i">
                <template v-if="typeof source === 'string'">
                  {{ source }}
                </template>

                <template v-else>
                  <strong>
                    {{ source.source || source.title || source.name || `Source ${i + 1}` }}
                  </strong>

                  <span v-if="source.pages?.length">
                    · p. {{ source.pages.join(", ") }}
                  </span>
                  <span v-else-if="source.page">
                    · p. {{ source.page }}
                  </span>

                  <div v-if="source.preview || source.snippet || source.excerpt" class="source-preview">
                    {{ source.preview || source.snippet || source.excerpt }}
                  </div>
                </template>
              </li>
            </ul>
          </div>

          <div v-else-if="showSources" class="sources-panel">
            <div class="sources-title">
              {{ $t("professional.sources") }}
            </div>
            <div class="source-preview">
              No sources available for this suggested reply.
            </div>
          </div>

          <div v-if="!isClosed" class="custom-input">
            <textarea
              v-model="editedReply"
              :disabled="!isEditing"
              :placeholder="$t('professional.writeMessage')"
              @keydown.enter.exact.prevent="sendReply"
            ></textarea>

            <div class="buttons">
              <AppButton
                variant="primary"
                :disabled="!editedReply.trim()"
                @click="sendReply"
              >
                {{ $t('send') }}
              </AppButton>

              <AppButton variant="neutral" @click="toggleEdit">
                {{ isEditing ? $t('professional.done') : $t('professional.edit') }}
              </AppButton>

              <AppButton
                v-if="!isClosed"
                variant="neutral"
                class="push-right"
                @click="returnToQueue"
              >
                {{ $t('professional.returnToQueue') }}
              </AppButton>

              <AppButton
                v-if="!isClosed"
                variant="danger"
                @click="showCloseConfirm = true"
              >
                {{ $t('professional.closeChat') }}
              </AppButton>
            </div>
          </div>
        </div>

        <!-- SIDEBAR -->
        <PatientCard
          v-if="chat?.patient_context"
          :patient="chat.patient_context"
          :summary="chat.chat_summary"
        />

      </div>
    </div>
        <!-- CLOSE CONFIRM MODAL -->
      <div v-if="showCloseConfirm"
      class="modal-overlay"
      @click.self="showCloseConfirm = false"
      >
        <div class="modal">

          <p class="modal-text">
            {{ $t("professional.confirmCloseText") }}
          </p>

          <div class="modal-actions">
            <AppButton variant="neutral" @click="showCloseConfirm = false">
              {{ $t("professional.cancel") }}
            </AppButton>

            <AppButton
              variant="danger"
              @click="showCloseConfirm = false; closeChat()"
            >
              {{ $t("professional.closeChat") }}
            </AppButton>
          </div>

        </div>
      </div>
  </div>

</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from "vue"
import { useRoute, useRouter } from "vue-router"
import HeaderBar from "@/components/ui/HeaderBar.vue"
import AppButton from "@/components/ui/AppButton.vue"
import ChatMessage from "@/components/chat/ChatMessage.vue"
import PatientCard from "@/components/PatientCard.vue"
import { useAuthStore } from "@/stores/authStore"
import { useProfessionalChatStore } from "@/stores/professionalChatStore"
import { chatSocket } from "@/services/chatSocket"

const route = useRoute()
const router = useRouter()

// route-parametrina tuleva chatin id
const chatId = route.params.id

const authStore = useAuthStore()
const chatStore = useProfessionalChatStore()

const currentUser = computed(() => authStore.user)

const messagesContainer = ref(null)
const showCloseConfirm = ref(false)

const chat = computed(() => chatStore.activeChat)
const editedReply = ref("")

// UI:n tilat: vastauskentän muokkaus ja lähteiden näkyvyys
const isEditing = ref(false)
const showSources = ref(false)

// jonot headerbaria varten
const waiting = computed(() => chatStore.getWaitingChats)
const closedToday = computed(() => chatStore.getClosedChats)

// tarkistaa onko keskustelu suljettu
const isClosed = computed(() => chat.value?.status === "closed")
const visibleMessages = computed(() => {
  return (chat.value?.messages || []).filter(m => m.sender !== 'info')
})

function messageKey(message, index) {
  return `${message?.id || message?._id || message?.created_at || "message"}-${index}`
}

// vaihtaa vastauskentän muokkaustilan
function toggleEdit() {
  isEditing.value = !isEditing.value
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

watch(
  () => chat.value?.messages?.length,
  () => {
    nextTick(() => {
      setTimeout(scrollToBottom, 0)
    })
  }
)

// hakee chatin ja jonot backendista
onMounted(async () => {
  try {
    if (!authStore.user) {
      await authStore.fetchUser()
    }

    await chatStore.openChat(chatId)

    editedReply.value = (chatStore.activeChat?.draft_response || "")
      .replace(/<br\s*\/?>/gi, "\n")

    connectWebsocket(chat.value)

    nextTick(() => {
      setTimeout(scrollToBottom, 0)
    })

  } catch (e) {
    console.error(e)
  }
})

onUnmounted(() => {
  chatSocket.disconnect()
})

const suggestedReplySources = computed(() => {
  return chat.value?.draft_sources || []
})

function connectWebsocket(chat) {
  if (!chat) return

  chatSocket.connect(chat.id, authStore.token, (data) => {
    console.log("Received websocket message:", data)
    if (data.sender !== authStore.getCurrentUserID) {
      // lisää uusi viesti chattiin
      chat.messages.push(data.message)
      // päivitä AI:n ehdotus vastauksesta
      if (data.type === "new_user_message" && data.draft) {
        chat.draft_response = data.draft
        chat.draft_sources = data.draft_sources || []
        editedReply.value = data.draft
      }
    }
  })
}

// lähettää ammattilaisen viestin
async function sendReply() {
  if (!editedReply.value.trim()) return
  if (!currentUser.value) return

  try {
    await chatStore.sendProfessionalMessage(editedReply.value)

    editedReply.value = ""
  } catch (e) {
    console.error(e)
  }
}

// palauttaa chatin jonoon
async function returnToQueue() {
  if (!chat.value) return

  const chatId = chat.value.id || chat.value._id

  try {
    await chatStore.unclaimChat(chatId)

    router.push("/professional")
  } catch (e) {
    console.error(e)
  }
}

// sulkee keskustelun
async function closeChat() {
  try {
    const chatId = chat.value.id || chat.value._id
    await chatStore.closeChat(chatId)
    router.push("/professional")
  } catch (e) {
    console.error(e)
  }
}

// navigoi takaisin jonoon
function goBack() {
  router.push("/professional")
}
</script>

<style scoped>
.page {
  height: 100vh;
  display: flex;
  overflow: hidden;
  flex-direction: column;
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

/* chat-näkymän pääcontainer */
.chat-container {
  flex: 1;
  min-height: 0;
  background: #e3f2fd;
  padding: clamp(16px, 2vw, 40px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

/* chat + sidebar layout */
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(200px, 19vw, 600px);
  gap: clamp(24px, 4vw, 120px);
  width: min(2000px, 70vw);
  margin-left: clamp(40px, 20vw, 700px);
  min-height: 0;
  height: 100%;
}

.chat-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 16px;
}

/* keskustelukortti */
.conversation-card {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: clamp(600px, 50vw, 1400px);
  min-height: 0;

  margin-left: auto;
}

/* tekstilaatikon header */
.reply-header {
  padding: 0 28px 8px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.reply-label {
  font-size: 13px;
  color: #7a869a;
  font-weight: 600;
  margin-left: 4px;
}

.divider {
  height: 1px;
  background: #e6eaf0;
}

/* CHAT INPUT AREA */
.custom-input {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  gap: 10px;
  padding: 0 28px 16px 28px;
}

.custom-input textarea {
  font-family:
    ui-sans-serif,
    system-ui,
    -apple-system,
    sans-serif;
  font-size: clamp(12px, 1vw, 18px);
  width: 100%;
  border-radius: 16px;
  border: 1px solid #e0e4ea;
  padding: 14px;
  min-height: 100px;
  background: #f0f7fc;
  box-sizing: border-box;
  resize: vertical;
}

.buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* SOURCES */
.sources-panel {
  background: #f8fafc;
  border: 1px solid #dbeafe;
  border-radius: 16px;

  padding: 16px 20px;
  margin: 12px 28px 16px 28px;
}

.sources-title {
  font-size: 13px;
  font-weight: 600;
  color: #2d445a;
  margin-bottom: 8px;
}

.sources-list {
  margin: 0;
  padding-left: 18px;
  font-size: 14px;
  color: #334155;
}

.sources-list li {
  margin-bottom: 6px;
}

.top-bar {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 10;

  padding: 12px clamp(16px, 2vw, 40px);
  pointer-events: auto;
}

.push-right {
  margin-left: auto;
}

/* CLOSE CONFIRM MODAL */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.modal {
  background: #ffffff;
  border-radius: 16px;
  width: 400px;
  max-width: 95%;
  padding: 24px;

  box-shadow: 0 20px 50px rgba(0,0,0,0.15);
}

.modal-text {
  margin: 0;
  font-size: 18px;
  line-height: 1.5;
  color: #0f172a;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;

  margin-top: 24px;
}
</style>
