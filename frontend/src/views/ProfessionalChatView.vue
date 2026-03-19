<template>

  <div class="page">

    <HeaderBar
    :queueCount="waiting.length"
    :closedCount="closedToday.length"
    :user="currentUser"
    :showLanguageSwitcher="false"
    :showCounts="true"
  />

    <div v-if="chatStore.loading.chat">Loading...</div>

    <div v-else class="chat-container">
      <div class="layout">

        <!-- Koko chat -->
        <div class="conversation-card">

          <!-- Viestihistoria -->
          <div v-if="chat && chat.messages" class="chat-messages">
            <ChatMessage
              v-for="(msg, i) in chat.messages"
              :key="i"
              :from="mapSender(msg.sender)"
              :text="msg.content"
            />
          </div>

          <div v-if="!isClosed" class="divider"></div>

          <!-- Vastausosio -->
          <div class="reply-header">

            <div class="reply-label">
              AI:N VASTAUSEHDOTUS
            </div>

            <AppButton
              variant="neutral"
              size="sm"
              @click="showSources = !showSources"
            >
              {{ showSources ? "Piilota lähteet" : "Näytä lähteet" }}
            </AppButton>

          </div>

          <!-- Lähteet -->
          <div v-if="showSources" class="sources-panel">

            <div class="sources-title">
              VIITTAUKSET
            </div>

            <ul class="sources-list">
              <li v-for="(s, i) in chat.sources" :key="i">
                {{ s }}
              </li>
            </ul>

          </div>

          <div v-if="!isClosed" class="custom-input">

            <textarea
              v-model="editedReply"
              :disabled="!isEditing"
              placeholder="Kirjoita viesti"
              @keydown.enter.exact.prevent="sendReply"
            ></textarea>

            <div class="buttons">
              <AppButton
                variant="primary"
                :disabled="!editedReply.trim()"
                @click="sendReply"
              >
                Lähetä
              </AppButton>

              <AppButton
                variant="neutral"
                @click="toggleEdit"
              >
                {{ isEditing ? "Valmis" : "Muokkaa viestiä" }}
              </AppButton>
            </div>

</div>

          <!-- Keskustelun hallintatoiminnot -->
          <div class="bottom-bar">

            <div class="left-actions">
              <AppButton
                variant="neutral"
                @click="goBack"
              >
                Palaa jonoon
              </AppButton>

              <AppButton
                v-if="!isClosed"
                variant="neutral"
                @click="returnToQueue"
              >
                Palauta jonoon
              </AppButton>
            </div>

            <div class="right-actions">
              <AppButton
                v-if="!isClosed"
                variant="danger"
                @click="closeChat"
              >
                Päätä keskustelu
              </AppButton>
            </div>

          </div>

        </div>

        <!-- Potilaan tiedot -->
        <div class="sidebar" v-if="chat?.patient_context">
          <h3>Potilaan tiedot</h3>

          <p><strong>Ikä:</strong> {{ chat.patient_context.age }}</p>
          <p><strong>Pituus:</strong> {{ chat.patient_context.height }}</p>
          <p><strong>Paino:</strong> {{ chat.patient_context.weight }}</p>

          <h4>Perussairaudet</h4>
          <p>{{ chat.patient_context.conditions?.join(", ") }}</p>

          <h4>AI-kooste</h4>
          <div v-html="formattedSummary"></div>

        </div>

      </div>
    </div>

  </div>

</template>

<script setup>

import { ref, onMounted, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import HeaderBar from "@/components/HeaderBar.vue"
import AppButton from "@/components/ui/AppButton.vue"
import ChatMessage from "@/components/chat/ChatMessage.vue"
import { useAuthStore } from "@/stores/authStore"
import { useProfessionalChatStore } from "@/stores/professionalChatStore"

const route = useRoute()
const router = useRouter()

// route-parametrina tuleva chatin id
const chatId = route.params.id

const authStore = useAuthStore()
const chatStore = useProfessionalChatStore()

const formattedSummary = computed(() => {
  if (!chat.value?.chat_summary) return ""

  return chat.value.chat_summary
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>")
})

function mapSender(sender) {
  if (sender === "user") return "self"
  if (sender === "assistant") return "other"
  if (sender === "professional") return "other"
  return "other"
}

const currentUser = computed(() => authStore.user)

const chat = computed(() => chatStore.activeChat)
const editedReply = ref("")

// UI:n tilat: vastauskentän muokkaus ja lähteiden näkyvyys
const isEditing = ref(false)
const showSources = ref(false)

// jonot headerbaria varten
const waiting = computed(() => chatStore.queues.waiting)
const closedToday = computed(() => chatStore.queues.closed)

// tarkistaa onko keskustelu suljettu
const isClosed = computed(() => chat.value?.status === "closed")

// vaihtaa vastauskentän muokkaustilan
function toggleEdit() {
  isEditing.value = !isEditing.value
}

// hakee chatin ja jonot backendista
onMounted(async () => {
  try {
    if (!authStore.user) {
      await authStore.fetchUser()
    }

    await chatStore.openChat(chatId)
    await chatStore.initializeQueues()

    editedReply.value = chatStore.activeChat?.draft_response || ""

  } catch (e) {
    console.error(e)
  }
})

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

.page{
  height:100vh;
  display:flex;
  flex-direction:column;
  overflow:hidden;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
}

/* chat-näkymän pääcontainer */
.chat-container{
  flex:1;
  min-height:0;
  background:#e3f2fd;
  padding:32px;
  display:flex;
  flex-direction:column;
  overflow:hidden;
}

/* chat + sidebar layout */
.layout{
  display:grid;
  grid-template-columns: minmax(0,1fr) 350px;
  gap:150px;

  width:100%;
  flex:1;
  min-height:0;
}

.chat-messages {
  max-width: 1200px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
  width: 90%;
  margin: 0 auto;
}

/* keskustelukortti */
.conversation-card{
  display:flex;
  flex-direction:column;
  max-width:1200px;
  height:100%;
  width:100%;
  margin-left:auto;
  min-height:0;
}

/* tekstilaatikon header */
.reply-header{
  padding:0 28px 8px 28px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-top:12px;
}

.reply-label{
  font-size:13px;
  color:#7a869a;
  font-weight:600;
  margin-left:4px;
}

.divider{
  height:1px;
  background:#e6eaf0;
}

/* potilaan tiedot -sivupalkki */
.sidebar{
  background:white;
  border-radius:24px;
  padding:28px;
  box-shadow:0 10px 30px rgba(0,0,0,0.05);
  display:flex;
  flex-direction:column;
  gap:18px;
  max-height: 100%;
  overflow-y: auto;
  margin-left: -100px;
}

.sidebar h3{
  font-size:18px;
  font-weight:600;
  margin-bottom:4px;
}

.sidebar h4{
  font-size:14px;
  font-weight:600;
  margin-top:12px;
  margin-bottom:2px;
}

/* tekstiblokit */
.sidebar p{
  font-size:14px;
  line-height:1.5;
  color:#2b2f36;
}

/* potilaan perustiedot */
.sidebar p strong{
  display:inline-block;
  min-width:70px;
  font-weight:600;
}

/* keskustelun hallintapalkki */
.bottom-bar{
  border-top:1px solid #e6eaf0;
  padding:18px 28px;

  display:flex;
  align-items:center;
  justify-content:space-between;

  max-width:1200px;
  width:100%;
  margin-left:auto;
}

.left-actions{
  display:flex;
  gap:12px;
}

/* CHAT INPUT AREA */
.custom-input {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 0 28px 16px 28px;
}

.custom-input textarea {
  font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
  width: 100%;
  border-radius: 16px;
  border: 1px solid #e0e4ea;
  padding: 14px;
  font-size: 18px;
  min-height: 100px; 
  background: #f0f7fc;
  box-sizing: border-box;
  resize: none;  
}

.buttons {
  display: flex;
  gap: 10px;
}

/* SOURCES */
.sources-panel{
  background:#f8fafc;
  border:1px solid #dbeafe;
  border-radius:16px;

  padding:16px 20px;
  margin:12px 28px 16px 28px;
}

.sources-title{
  font-size:13px;
  font-weight:600;
  color:#64748b;
  margin-bottom:8px;
}

.sources-list{
  margin:0;
  padding-left:18px;
  font-size:14px;
  color:#334155;
}

.sources-list li{
  margin-bottom:6px;
}

@media (max-width:1100px){
  .layout{
    grid-template-columns:1fr;
    gap:24px;
  }

  .sidebar{
    order:-1;
  }
}

</style>