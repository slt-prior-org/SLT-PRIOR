<!-- Ammattilaisen dashboard: chat-jonot ja esikatselu -->

<template>
  <HeaderBar
    :queueCount="waiting.length"
    :closedCount="closedToday.length"
    :user="currentUser"
    :showLanguageSwitcher="false"
    :showCounts="true"
  />

  <div v-if="chatStore.loading.queues" class="loading">Loading...</div>

  <div v-else class="dashboard-container">

    <!-- Päivämäärä ja näkymän otsikko -->
    <div class="workspace-header">

      <div class="workspace-label">AMMATTILAISEN TYÖPÖYTÄ</div>

      <div class="date-chip">
        {{ formattedToday }}
      </div>

    </div>

    <div class="divider"></div>

    <!-- Chat-jonot -->
    <div class="main-card">

      <div class="main-card-header">
        <h2>Päivän tehtäväjono</h2>

        <AppButton variant="primary" @click="openNext">
          Avaa seuraava →
        </AppButton>
      </div>

      <div class="sections-scroll">

        <div class="section">

          <div class="section-header">
            <span>AKTIIVISET</span>
            <div class="section-count">{{ activeChats.length }}</div>
          </div>

          <div v-if="!activeChats.length" class="empty">
            Ei tapauksia tässä osiossa
          </div>

          <div v-else class="chat-grid">

            <div
              v-for="chat in activeChats"
              :key="chat.id"
              class="chat-card"
              :class="chat.status"
              @click="chat.status === 'waiting_for_professional' ? openPreview(chat) : router.push(`/professional/chat/${chat.id}`)"
            >

              <div class="chat-body">
                <b>Potilas #{{ chat.id }}</b>
                <p>{{ chat.last_message ?? "Ei viestiä" }}</p>
              </div>

              <div class="chat-meta">

                <div class="time">
                  {{ formatTime(chat.updated_at) }}
                </div>

                <div
                  v-if="chat.status === 'in_progress'"
                  class="chat-status"
                >
                  Käsittelyssä
                </div>

              </div>

            </div>

          </div>
        </div>                
      </div>

      <div class="history-toggle">

        <AppButton
          variant="neutral"
          @click="showClosed = !showClosed"
        >
          {{ showClosed ? "Piilota käsitellyt" : `Näytä käsitellyt (${closedToday.length})` }}
        </AppButton>

      </div>

      <div v-if="showClosed" class="section">

        <div class="section-header">
          <span>KÄSITELTY TÄNÄÄN</span>
        </div>

        <div class="chat-grid">

          <div
            v-for="chat in closedToday"
            :key="chat.id"
            class="chat-card closed"
            @click="router.push(`/professional/chat/${chat.id}`)"
          >
            <div class="chat-body">
              <b>Potilas #{{ chat.id }}</b>
              <p>{{ chat.last_message ?? "Ei viestiä" }}</p>
            </div>

            <div class="time">
              {{ formatTime(chat.updated_at) }}
            </div>

          </div>

        </div>

      </div>

    </div>

    <!-- Esikatselumodal odottaville chateille -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal">

        <h3>Chatin esikatselu</h3>

        <div class="preview-card">

          <div class="preview-header">

            <div class="preview-patient">
              Potilas #{{ selectedChat?.id }}
            </div>

            <div class="preview-time">
              {{ formatTime(selectedChat?.updated_at) }}
            </div>

          </div>

          <div class="preview-message">
            {{ selectedChat?.last_message || "Ei vielä viestejä" }}
          </div>

        </div>

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

    <div class="dashboard-footer">
      <img src="@/assets/newlogo.png" alt="Logo" class="footer-logo">
    </div>

  </div>

</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue"
import { useRouter } from "vue-router"
import { useProfessionalChatStore } from "@/stores/professionalChatStore"
import HeaderBar from "@/components/HeaderBar.vue"
import AppButton from "@/components/ui/AppButton.vue"
import { useAuthStore } from "@/stores/authStore"

// käyttäjän sessio ja tiedot
const authStore = useAuthStore()

const chatStore = useProfessionalChatStore()

const currentUser = computed(() => authStore.user)

const activeChats = computed(() => [
  ...chatStore.queues.in_progress,
  ...chatStore.queues.waiting
])

const waiting = computed(() => chatStore.queues.waiting)
const closedToday = computed(() => chatStore.queues.closed)

const showClosed = ref(false)

const router = useRouter()

// valittu chat esikatselussa
const selectedChat = ref(null)

// modalin näkyvyys
const showModal = ref(false)

// päivämäärä headeriin
const formattedToday = computed(() => {
  const today = new Date().toLocaleDateString("fi-FI", {
    weekday: "long",
    day: "numeric",
    month: "numeric",
    year: "numeric"
  })
  return today.charAt(0).toUpperCase() + today.slice(1)
})

let refreshInterval

// hakee käyttäjän session ja chat-jonot
onMounted(async () => {
  try {
    if (!authStore.user) {
      await authStore.fetchUser()
    }

    await chatStore.initializeQueues()

    refreshInterval = setInterval(() => {
      chatStore.initializeQueues()
    }, 60000)

  } catch (e) {
    console.error("Failed to fetch queues", e)
  }
})

onUnmounted(() => {
  clearInterval(refreshInterval)
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
async function claimChat() {
  if (!selectedChat.value) return

  const chatId = selectedChat.value.id || selectedChat.value._id

  try {
    await chatStore.claimChat(chatId)

    showModal.value = false
    router.push(`/professional/chat/${chatId}`)

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

// muotoilee ajan backendista
function formatTime(date) {
  if (!date) return ""

  return new Date(date).toLocaleTimeString("fi-FI", {
    hour: "2-digit",
    minute: "2-digit"
  })
}

</script>

<style scoped>

.dashboard-container{
  background:#e3f2fd;
  min-height:calc(100vh - 72px);
  padding:32px 20px;
  display:flex;
  flex-direction:column;
  overflow:hidden;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
}

.workspace-header{
  max-width:900px;
  width:100%;
  margin:0 auto 10px auto;
  display:flex;
  justify-content:space-between;
  align-items:center;
}

.workspace-label{
  font-size:14px;
  letter-spacing:.08em;
  color:#666666;
  font-weight:600;
}

.date-chip{
  background:white;
  padding:10px 16px;
  border-radius:10px;
  font-size:13px;
  color:#404040;
  box-shadow:0 4px 12px rgba(0,0,0,0.05);
}

.divider{
  max-width:900px;
  width:100%;
  margin:12px auto 24px auto;
  border-top:1px solid #b3b3b3;
}

/* chat-lista korttina */
.main-card{
  max-width:900px;
  width:100%;
  margin:35px auto;
  background:white;
  border-radius:32px;
  padding:28px 32px;
  box-shadow:0 12px 40px rgba(0,0,0,0.05);
  display:flex;
  flex-direction:column;
}

.main-card-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:24px;
  gap:20px;
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
  display:flex;
  flex-direction:column;
  gap:12px;

  max-height:400px;
  overflow-y:auto;
}

/* chat-kortit */
.chat-card{
  display:flex;
  align-items:stretch;
  width:100%;
  gap:14px;
  background:white;
  padding:14px 16px;
  border-radius:18px;
  border:1px solid #e5e7eb;
  box-shadow:none;
  cursor:pointer;
  transition:.2s;
  position:relative;
}

.chat-card:hover{
  transform:translateY(-3px);
}

.chat-card.in_progress{
  background:#f0f9ff;
  border-color:#93c5fd;
}

.chat-body{
  flex:1;
}

.chat-body p{
  font-size:13px;
  color:#404040;
  margin-top:2px;
}

.chat-body b{
  font-size:13px;
  color:#262626;
  margin-top:2px;
}

.chat-status{
  font-size:11px;
  font-weight:600;
  color:#2563eb;
  background:#eff6ff;
  padding:2px 6px;
  border-radius:6px;
  position:absolute;
  right:12px;
  bottom:12px;
}

.chat-meta{
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  align-items:flex-end;
  height:100%;
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

.dashboard-footer{
  display:flex;
  justify-content:center;
  margin-top:5px;
}

.footer-logo{
  height:200px;
  opacity:0.8;
}

</style>