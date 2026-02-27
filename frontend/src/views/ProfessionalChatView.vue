<template>

  <div class="page">

    <NewHeaderBar
      :queueCount="waiting.length"
      :closedCount="closedToday.length"
      :user="currentUser"
    />

    <div v-if="!chat">Loading...</div>

    <div v-else class="chat-container">
      <div class="layout">

        <!-- Koko chat -->
        <div class="conversation-card">

          <!-- Viestihistoria -->
          <ChatMessageList
            v-if="chat && chat.messages"
            :messages="chat.messages"
          />

          <div v-if="!isClosed" class="divider"></div>

          <!-- Vastausosio -->
          <div v-if="!isClosed" class="reply-header">
            <div class="reply-label">AI:n vastausehdotus</div>

            <AppButton
              variant="neutral"
              size="sm"
              @click="showSources = true"
            >
              Näytä lähteet
            </AppButton>
          </div>

          <ChatInputBar
            v-if="!isClosed"
            v-model="editedReply"
            :disabled="!isEditing"
            :showEdit="true"
            :isEditing="isEditing"
            placeholder="AI:n ehdottama vastaus..."
            @send="sendReply"
            @toggle-edit="toggleEdit"
          />

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
        <div class="sidebar" v-if="chat?.patient">
          <h3>Potilaan tiedot</h3>

          <p><strong>ID:</strong> {{ chat.patient.id }}</p>
          <p><strong>Ikä:</strong> {{ chat.patient.age }}</p>
          <p><strong>Sukupuoli:</strong> {{ chat.patient.gender }}</p>

          <h4>Perussairaudet</h4>
          <p>{{ chat.patient.conditions }}</p>

          <h4>Lääkitys</h4>
          <p>{{ chat.patient.medication }}</p>

          <h4>AI-kooste</h4>
          <p>{{ chat.summary }}</p>

          <AppButton variant="neutral">
            Avaa potilastiedot
          </AppButton>
        </div>

      </div>
    </div>

    <!-- Lähteiden modaali -->
    <div v-if="showSources" class="modal">
      <div class="modal-content">
        <h4>Lähteet</h4>
        <ul>
          <li v-for="(s, i) in chat.sources" :key="i">{{ s }}</li>
        </ul>
        <AppButton variant="neutral" size="sm" @click="showSources = false">
          Sulje
        </AppButton>
      </div>
    </div>

  </div>

</template>

<script setup>

import { ref, onMounted, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import NewHeaderBar from "@/components/NewHeaderBar.vue"
import ChatInputBar from "@/components/NewChatInputBar.vue"
import AppButton from "@/components/NewAppButton.vue"
import ChatMessageList from "@/components/NewChatMessageList.vue"
import { useAuthStore } from "@/stores/authStore"

import {
  fetchChat,
  addProfessionalMessage,
  close as closeChatApi,
  fetchQueues
} from "@/services/professionalChatService"

const route = useRoute()
const router = useRouter()

// route-parametrina tuleva chatin id
const chatId = route.params.id

const authStore = useAuthStore()

// mock-käyttäjä fallbackiksi jos backend ei vielä palauta käyttäjää
const mockUser = {
  id: "mockProfessional1",
  name: "Aku Ankka",
  role: "professional"
}

const currentUser = computed(() => authStore.user ?? mockUser)

// chat-data ja ammattilaisen muokattava vastaus
const chat = ref(null)
const editedReply = ref("")

// UI:n tilat: vastauskentän muokkaus ja lähteiden näkyvyys
const isEditing = ref(false)
const showSources = ref(false)

// jonot headerbaria varten
const queues = ref(null)
const waiting = computed(() => queues.value?.waiting || [])
const closedToday = computed(() => queues.value?.closed || [])

// tarkistaa onko keskustelu suljettu
const isClosed = computed(() => chat.value?.status === "closed")

// vaihtaa vastauskentän muokkaustilan
function toggleEdit() {
  isEditing.value = !isEditing.value
}

// mock-chat kehitystä varten
const mockChat = {
  chat_id: "mock1",
  isMock: true,
  status: "in_progress",
  ai_suggested_reply: "Suosittelen hakeutumaan lääkärin arvioon.",
  patient: {
    id: "mockPatient",
    age: 58,
    gender: "Mies",
    conditions: "Kohonnut verenpaine",
    medication: "Metoprololi"
  },
  summary: "Rintakipua rasituksessa, riskitekijöitä",
  sources: ["ESC guideline", "Käypä hoito"],
  messages: [
    { sender: "user", content: "Minulla on rintakipua rasituksessa" },
    { sender: "bot", content: "Rintakipu rasituksessa voi liittyä sydämen hapenpuutteeseen." }
  ]
}

// hakee chatin ja jonot backendista (mukana mock-toteutus)
onMounted(async () => {
  try {
    if (chatId.startsWith("mock")) {
      chat.value = mockChat
      editedReply.value = mockChat.ai_suggested_reply
      return
    }

    const data = await fetchChat(chatId)

    chat.value = data ?? mockChat
    editedReply.value = chat.value.ai_suggested_reply || ""
  } catch (e) {
    chat.value = mockChat
    editedReply.value = mockChat.ai_suggested_reply
  }

  try {
  queues.value = await fetchQueues()
  } catch {
    queues.value = { waiting: [], closed: [] }
  }
})

// lähettää ammattilaisen viestin
async function sendReply() {
  if (!editedReply.value.trim()) return

  // mock, ei kutsuta backendia
  if (chat.value.isMock) {
    if (!chat.value.messages) chat.value.messages = []

    chat.value.messages.push({
      sender: "professional",
      content: editedReply.value
    })

    editedReply.value = ""
    return
  }

  // backend mukana
  try {
    await addProfessionalMessage(chat.value._id, {
      content: editedReply.value,
      professional_id: currentUser.value.id
    })

    if (!chat.value.messages) chat.value.messages = []

    chat.value.messages.push({
      sender: "professional",
      content: editedReply.value
    })

    editedReply.value = ""
  } catch (e) {
    console.error(e)
  }
}

// palauttaa chatin jonoon (backend vielä puuttuu)
async function returnToQueue() {
  // await returnChatToQueue(chat.value.chat_id)
  console.log("Return to queue clicked (backend not implemented)")
  router.push("/professional")
}

// sulkee keskustelun
async function closeChat() {
  // mock -> ohitetaan backend
  if (chat.value.isMock) {
    chat.value.status = "closed"
    router.push("/professional")
    return
  }

  // backend mukana
  try {
    await closeChatApi(chat.value._id)
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
}

/* chat-näkymän pääcontainer */
.chat-container{
  flex:1;
  min-height:0;
  background:#f8fafc;
  padding:32px;
  display:flex;
  flex-direction:column;
  overflow:hidden;
}

/* chat + sidebar layout */
.layout{
  display:grid;
  grid-template-columns: minmax(0,1fr) 380px;
  gap:150px;

  width:100%;
  flex:1;
  min-height:0;
}

/* keskustelukortti */
.conversation-card{
  display:flex;
  flex-direction:column;
  max-width:1100px;
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

  max-width:1100px;
  width:100%;
  margin-left:auto;
}

.left-actions{
  display:flex;
  gap:12px;
}

/* modal */
.modal{
  position:fixed;
  inset:0;
  background:rgba(0,0,0,0.35);
  display:flex;
  justify-content:center;
  align-items:center;
}

.modal-content{
  background:white;
  padding:24px;
  border-radius:20px;
  width:420px;
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