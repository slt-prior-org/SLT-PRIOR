<!-- Ammattilaisen dashboard: chat-jonot ja esikatselu -->

<template>
  <NewHeaderBar
    :queueCount="waiting.length"
    :closedCount="closedToday.length"
    :user="currentUser"
  />

  <div v-if="!chats" class="loading"></div>

  <div v-else class="dashboard-container">

    <!-- Päivämäärä ja näkymän otsikko -->
    <div class="workspace-header">

      <div class="workspace-left">
        <div class="workspace-label">AMMATTILAISEN TYÖPÖYTÄ</div>
      </div>

      <div class="date-chip">
        {{ today }}
      </div>

    </div>

    <!-- Chat-jonot -->
    <div class="main-card">

      <div class="main-card-header">
        <h2>Päivän tehtäväjono</h2>

        <AppButton variant="primary" @click="openNext">
          Avaa seuraava →
        </AppButton>
      </div>

      <div class="sections-scroll">

        <!-- Käsittelyssä olevat chatit -->
        <div class="section">
          <div class="section-header">
            <span>KÄSITTELYSSÄ</span>
            <div class="section-count">{{ inProgress.length }}</div>
          </div>

          <div v-if="!inProgress.length" class="empty">
            Ei tapauksia tässä osiossa
          </div>

          <div v-else class="chat-grid">
            <div
              v-for="chat in inProgress"
              :key="chat._id"
              class="chat-card"
              @click="router.push(`/professional/chat/${chat._id}`)"
            >
              <div class="avatar"></div>

              <div class="chat-body">
                <strong>Potilas #{{ chat._id }}</strong>
                <p>{{ chat.last_message ?? "Ei viestiä" }}</p>
              </div>

              <div class="time">
                {{ formatTime(chat.updated_at) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Odottavat chatit -->
        <div class="section">
          <div class="section-header">
            <span>ODOTTAA</span>
            <div class="section-count">{{ waiting.length }}</div>
          </div>

          <div class="chat-grid">
            <div
              v-for="chat in waiting"
              :key="chat._id"
              class="chat-card"
              @click="openPreview(chat)"
            >
              <div class="avatar"></div>

              <div class="chat-body">
                <strong>Potilas #{{ chat._id }}</strong>
                <p>{{ chat.last_message ?? "Ei viestiä" }}</p>
              </div>

              <div class="time">
                {{ formatTime(chat.updated_at) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Käsitellyt chatit -->
        <div class="section">
          <div class="section-header">
            <span>KÄSITELTY TÄNÄÄN</span>
            <div class="section-count">{{ closedToday.length }}</div>
          </div>

          <div v-if="!closedToday.length" class="empty">
            Ei tapauksia tässä osiossa
          </div>

          <div v-else class="chat-grid">
            <div
              v-for="chat in closedToday"
              :key="chat._id"
              class="chat-card closed"
              @click="router.push(`/professional/chat/${chat._id}`)"
            >
              <div class="avatar"></div>

              <div class="chat-body">
                <strong>Potilas #{{ chat._id }}</strong>
                <p>{{ chat.last_message ?? "Ei viestiä" }}</p>
              </div>

              <div class="time">
                {{ formatTime(chat.updated_at) }}
              </div>
            </div>
          </div>
        </div>
                
      </div>

    </div>

    <!-- Esikatselumodal odottaville chateille -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal">

        <h3>Chatin esikatselu</h3>
        <p><strong>ID:</strong> {{ selectedChat?._id }}</p>

        <div class="modal-actions">
          <AppButton variant="primary" @click="claimChat">
            Ota käsittelyyn
          </AppButton>

          <AppButton variant="neutral" @click="closeModal">
            Sulje
          </AppButton>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue"
import { useRouter } from "vue-router"
import { fetchQueues, claim } from "@/services/professionalChatService"
import NewHeaderBar from "@/components/NewHeaderBar.vue"
import AppButton from "@/components/NewAppButton.vue"
import { useAuthStore } from "@/stores/authStore"

// käyttäjän sessio ja tiedot
const authStore = useAuthStore()

// mock-käyttäjä
const mockUser = {
  id: "mockProfessional1",
  name: "Aku Ankka",
  role: "professional"
}

// headerbar käyttää backend-käyttäjää tai mockia
const currentUser = computed(() => authStore.user ?? mockUser)

const router = useRouter()

// chat-jonojen tila
const chats = ref(null)

// valittu chat esikatselussa
const selectedChat = ref(null)

// modalin näkyvyys
const showModal = ref(false)

// Backend palauttaa valmiiksi ryhmitellyt jonot
const inProgress = computed(() => chats.value?.in_progress || [])
const waiting = computed(() => chats.value?.waiting || [])
const closedToday = computed(() => chats.value?.closed || [])

// päivämäärä headeriin
const today = new Date().toLocaleDateString("fi-FI", {
  day: "numeric",
  month: "numeric",
  year: "numeric"
})


// mock-jonot UI-kehitystä varten
const mockQueues = {
  in_progress: [
    {
      _id: "mock1",
      isMock: true,
      patient_name: "Potilas #4721",
      last_message: "Minulla on ollut rintakipua rasituksessa",
      status: "in_progress"
    }
  ],
  waiting: [
    {
      _id: "mock2",
      isMock: true,
      patient_name: "Potilas #3892",
      last_message: "Sykemittari näyttää epäsäännöllistä sykettä",
      status: "waiting_for_professional"
    },
    {
      _id: "mock3",
      isMock: true,
      patient_name: "Potilas #5614",
      last_message: "Verenpaineeni on ollut koholla",
      status: "waiting_for_professional"
    }
  ],
  closed: [
    {
      _id: "mock4",
      isMock: true,
      patient_name: "Potilas #2873",
      last_message: "Lääkkeen sivuvaikutukset",
      status: "closed"
    }
  ]
}

// hakee käyttäjän session ja chat-jonot
// tällä hetkellä käyttää mock-dataa, jos backend ei vastaa tai jonot tyhjät
onMounted(async () => {
  try {
    if (!authStore.user) {
      await authStore.fetchUser()
    }

    const data = await fetchQueues()

    if (
      !data ||
      (!data.in_progress?.length &&
       !data.waiting?.length &&
       !data.closed?.length)
    ) {
      chats.value = mockQueues
      return
    }

    chats.value = data

  } catch (e) {
    console.log("Backend not available -> mock queues")
    chats.value = mockQueues
  }
})

// avaa chatin esikatselu
function openPreview(chat) {
  selectedChat.value = chat
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

// varaa chatin ja navigoi siihen
// mock ohittaa backendin
async function claimChat() {
  if (!selectedChat.value) return

  if (selectedChat.value.isMock) {
    showModal.value = false
    router.push(`/professional/chat/${selectedChat.value._id}`)
    return
  }

  try {
    await claim(selectedChat.value._id, currentUser.value.id)

    showModal.value = false
    router.push(`/professional/chat/${selectedChat.value._id}`)

  } catch (e) {
    console.error(e)
  }
}

// avaa seuraavan odottavan chatin esikatselun
function openNext() {
  if (waiting.value.length > 0) {
    openPreview(waiting.value[0])
  }
}

// muotoilee ajan backendista, fallback mock
function formatTime(date) {
  if (!date) return "11:45" // mock fallback

  return new Date(date).toLocaleTimeString("fi-FI", {
    hour: "2-digit",
    minute: "2-digit"
  })
}

</script>

<style scoped>

.dashboard-container{
  background:#f5f7fb;
  height:calc(100vh - 72px);
  padding:32px 20px;
  display:flex;
  flex-direction:column;
  overflow:hidden;
}

.workspace-header{
  max-width:1100px;
  width:100%;
  margin:0 auto 18px auto;
  display:flex;
  justify-content:space-between;
  align-items:center;
}

.workspace-label{
  font-size:12px;
  letter-spacing:.08em;
  color:#7a869a;
  font-weight:600;
}

.date-chip{
  background:white;
  padding:10px 16px;
  border-radius:20px;
  font-size:13px;
  box-shadow:0 4px 12px rgba(0,0,0,0.05);
}

/* chat-lista korttina */
.main-card{
  max-width:1100px;
  margin:auto;
  background:white;
  border-radius:32px;
  padding:28px 32px;
  box-shadow:0 12px 40px rgba(0,0,0,0.05);
  display:flex;
  flex-direction:column;
  flex:1;
  min-height:0;
}

.main-card-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:24px;
  gap:20px;
}

/* scrollattava jonolista */
.sections-scroll{
  flex:1;
  overflow-y:auto;
  padding-right:8px;
}

.sections-scroll::-webkit-scrollbar{
  width:8px;
}
.sections-scroll::-webkit-scrollbar-thumb{
  background:#d7dce5;
  border-radius:10px;
}

.section{
  margin-bottom:26px;
}

.section-header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  font-size:12px;
  color:#6b7a90;
  margin-bottom:14px;
}

.section-count{
  background:#eef1f6;
  padding:2px 10px;
  border-radius:20px;
  font-size:12px;
}

.empty{
  border:1px dashed #d9dee7;
  padding:24px;
  text-align:center;
  border-radius:16px;
  color:#7a869a;
  font-size:13px;
}

.chat-grid{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:16px;
}

/* chat-kortit */
.chat-card{
  display:flex;
  align-items:center;
  gap:14px;
  background:#f9fbff;
  padding:14px 16px;
  border-radius:18px;
  box-shadow:0 4px 12px rgba(0,0,0,0.04);
  cursor:pointer;
  transition:.2s;
}

.chat-card:hover{
  transform:translateY(-3px);
}

.avatar{
  width:32px;
  height:32px;
  border-radius:50%;
  background:#e8eefc;
}

.chat-body{
  flex:1;
}

.chat-body p{
  font-size:13px;
  color:#6b7a90;
  margin-top:2px;
}

.time{
  font-size:12px;
  color:#7a869a;
}

.chat-card.closed{
  opacity:.6;
}

/* chatin esikatselumodal */

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
  background: white;
  padding: 24px;
  border-radius: 12px;
  width: 360px;
}

.modal-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

/* footer */
.logo-space{
  height:80px;
  flex-shrink:0;
}

/* responsive */
@media(max-width:1000px){
  .chat-grid{
    grid-template-columns:repeat(2,1fr);
  }
}

@media(max-width:650px){
  .chat-grid{
    grid-template-columns:1fr;
  }
}

</style>