<template>
  <header class="header">
    <div
      v-if="
        loginNotification || registerNotification || profileUpdateNotification
      "
      class="login-toast"
    >
      <span class="toast-icon">✔️</span>
      <span class="toast-text">
        {{
          loginNotification || registerNotification || profileUpdateNotification
        }}
      </span>
    </div>

    <AppButton :class="{ 'sidebar-toggle': true, 'hidden': sidebarOpen || !isPatient }" variant="neutral" @click="toggleSidebar">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display: inline-block; vertical-align: middle;">
        <rect y="4" width="24" height="2" rx="1" />
        <rect y="11" width="24" height="2" rx="1" />
        <rect y="18" width="24" height="2" rx="1" />
      </svg>
    </AppButton>

    <div class="left" :style="{ left: sidebarOpen ? '280px' : 'clamp(12px, 2vw, 28px)' }">
      <div v-if="loggedIn" class="user" :style="{ marginLeft: (isPatient && !sidebarOpen) ? '70px' : '20px' }">
        <strong>{{ fullName }}</strong>
        <small>{{ userRole }}</small>
      </div>
    </div>

    <div class="center">
      <button class="logo-btn" @click="startNewChat" :title="$t('sidebar.newChat')">
        <img src="@/assets/new_logo.png" alt="HeartWise Logo" class="logo" />
      </button>
    </div>

    <div class="right">
      <div v-if="showCounts" class="counts">
        <span class="badge">
          {{ $t("professional.inQueue") }} {{ queueCount }}
        </span>
        <span class="badge light">
          {{ $t("professional.done") }} {{ closedCount }}
        </span>
      </div>

      <AppButton
        v-if="showLanguageSwitcher"
        class="gear language-toggle"
        variant="neutral"
        @click="toggleLanguage"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          <path d="M2 12h20" />
        </svg>
        {{ languageToggleLabel }}
      </AppButton>

      <AppButton
        v-if="loggedIn"
        class="gear"
        variant="neutral"
        @click="toggleMenu"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" style="display: inline-block; vertical-align: middle;">
          <path d="M10.325 4.317c.426 -1.756 2.924 -1.756 3.35 0a1.724 1.724 0 0 0 2.573 1.066c1.543 -.94 3.31 .826 2.37 2.37a1.724 1.724 0 0 0 1.065 2.572c1.756 .426 1.756 2.924 0 3.35a1.724 1.724 0 0 0 -1.066 2.573c.94 1.543 -.826 3.31 -2.37 2.37a1.724 1.724 0 0 0 -2.572 1.065c-.426 1.756 -2.924 1.756 -3.35 0a1.724 1.724 0 0 0 -2.573 -1.066c-1.543 .94 -3.31 -.826 -2.37 -2.37a1.724 1.724 0 0 0 -1.065 -2.572c-1.756 -.426 -1.756 -2.924 0 -3.35a1.724 1.724 0 0 0 1.066 -2.573c-.94 -1.543 .826 -3.31 2.37 -2.37c1 .608 2.296 .07 2.572 -1.065z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      </AppButton>

      <AppButton
        v-else
        class="login-btn"
        size="lg"
        variant="primary"
        @click="openAuthModal('login')"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0;">
          <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
          <polyline points="10 17 15 12 10 7" />
          <line x1="15" y1="12" x2="3" y2="12" />
        </svg>
        {{ $t("settings.login") }}
      </AppButton>

      <SettingsDropdownMenu
        v-if="menuOpen"
        :items="dropdownItems"
        @close="menuOpen = false"
      />
    </div>
  </header>

  <AuthModal
    :show="showAuth"
    @close="showAuth = false"
    @login-success="handleLoginSuccess"
    @register-success="handleRegisterSuccess"
  />

  <HealthProfileModal
    v-if="healthProfileOpen"
    @close="healthProfileOpen = false"
    @profile-update-success="handleProfileUpdateSuccess"
  />
</template>

<script setup>
import { computed, ref } from "vue"
import { useRouter } from "vue-router"
import { useI18n } from "vue-i18n"
import AppButton from "./AppButton.vue"
import AuthModal from "../auth/AuthModal.vue"
import SettingsDropdownMenu from "../settings/SettingsDropdownMenu.vue"
import HealthProfileModal from "../settings/HealthProfileModal.vue"

import { useAuthStore } from "@/stores/authStore"

// Komponentin ottamat vastaanottamat tiedot
defineProps({
  queueCount: Number,
  closedCount: Number,
  sidebarOpen: Boolean,
  showLanguageSwitcher: {
    type: Boolean,
    default: true,
  },
  showCounts: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['sidebar-toggle', 'start-new-chat'])

// Alustetaan kielituki ja käyttäjästore
const auth = useAuthStore()
const router = useRouter()
const i18n = useI18n()
const { t } = useI18n()

const loginNotification = ref("")
const registerNotification = ref("")
const profileUpdateNotification = ref("")

// Tarkistetaan onko käyttäjä kirjautunut sisään
const loggedIn = computed(() => auth.isAuthenticated)
const isPatient = computed(() => auth.isPatient)
const showAuth = ref(false)
const user = computed(() => auth.user)

// Yhdistetään etu- ja sukunimi, jos ne löytyvät
const fullName = computed(() => {
  const u = user.value
  if (!u) return ""

  const name = [u.first_name, u.last_name].filter(Boolean).join(" ").trim()

  return name || u.name || u.email || "..."
})

// Käytetään käännettyä roolia
const userRole = computed(() => {
  const role = user.value?.role
  if (!role) return ""
  return t(`roles.${role}`)
})

// Funktio sivupalkin kytkelemiseen
function toggleSidebar() {
  emit('sidebar-toggle')
}

// Funktio uuden chatin aloitukseen
function startNewChat() {
  emit('start-new-chat')
}

// Funktio sovelluksen kielen vaihtamiseen
function switchLanguage(lang) {
  i18n.locale.value = lang
}

// Computed property for language toggle button label
const languageToggleLabel = computed(() => {
  return i18n.locale.value === 'fi' ? 'EN' : 'FI'
})

// Function to toggle language
function toggleLanguage() {
  const newLang = i18n.locale.value === 'fi' ? 'en' : 'fi'
  switchLanguage(newLang)
}

// Valikkojen ja modaalien näkyvyyden hallinta
const menuOpen = ref(false)
const healthProfileOpen = ref(false)
const initialSettingsSection = ref("personalInfo")

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

// Funktio kirjautumis- ja rekisteröintimodaalin avaamiseen
function openAuthModal(section) {
  if (!loggedIn.value) {
    showAuth.value = true
    menuOpen.value = false
    return
  }

  initialSettingsSection.value = section
  menuOpen.value = false
}

// Funktio kirjautumisen onnistumisilmoituksen näyttämiseen
function handleLoginSuccess() {
  showAuth.value = false
  loginNotification.value = t("loginStatus.success")

  setTimeout(() => {
    loginNotification.value = ""
  }, 4000)
}

// Funktio rekisteröitymisen onnistumisilmoituksen näyttämiseen
function handleRegisterSuccess() {
  showAuth.value = false
  registerNotification.value = t("registerStatus.success")

  setTimeout(() => {
    registerNotification.value = ""
  }, 4000)
}

// Funktio onnistuneen profiilipäivityksen ilmoituksen näyttämiseen
function handleProfileUpdateSuccess() {
  profileUpdateNotification.value = t("healthProfileStatus.success")

  setTimeout(() => {
    profileUpdateNotification.value = ""
  }, 4000)
}

function openHealthProfile() {
  menuOpen.value = false
  healthProfileOpen.value = true
}

// Lasketaan pudotusvalikon kohteet kirjautumistilan mukaan
const dropdownItems = computed(() => {
  const items = []
  
  // Only show health profile option for patients
  if (isPatient.value) {
    items.push({
      key: "edit-health-profile",
      labelKey: "settings.editHealthProfile",
      action: () => openHealthProfile(),
    })
  }
  
  // Logout is always shown
  items.push({
    key: "logout",
    labelKey: "logout",
    action: () => handleLogout(),
  })
  
  return items
})

// Uloskirjautumisen hallinta
async function handleLogout() {
  try {
    await auth.logout()
    router.push("/")
  } catch (err) {
    console.error(err)
  }
}
</script>

<style scoped>
/* Yläpalkin asemointi ja ulkoasu */
.header {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: clamp(10px, 1.2vw, 16px) clamp(16px, 2vw, 28px);
  background: white;
  border-bottom: 1px solid #eee;
  z-index: 1002;
  transition: opacity 0.2s;
}

.header.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.left {
  position: absolute;
  left: clamp(12px, 2vw, 28px);
  display:flex; 
  align-items:center;
  transition: left 0.3s ease-out;
}

/* Sidebar, settings, and language buttons: WCAG AAA contrast */
.sidebar-toggle {
  position: absolute;
  left: clamp(12px, 2vw, 28px);
  z-index: 1001;
  width: 48px;
  height: 48px;
  min-width: 48px;
  padding: 0;
  background: #ffffff;
  border: 2px solid #eef1f6;
  border-radius: 16px;
  color: #0f172a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
  transition: all 0.2s ease;
  cursor: pointer;
}
.sidebar-toggle:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
  color: #0f172a;
}
.sidebar-toggle:focus-visible {
  outline: 2px solid #0f5791;
  outline-offset: 2px;
}

.sidebar-toggle.hidden {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}
.center {
  display: flex;
  gap: 12px;
  align-items: center;
}

.logo-btn {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  transition: all 0.2s ease;
  outline: none;
}

.logo-btn:hover {
  background: #f1f5f9;
}

.logo-btn:focus-visible {
  outline: 2px solid #0f5791;
  outline-offset: 2px;
}

.logo-btn:active {
  background: #e3e8f3;
}

.logo {
  max-height: clamp(30px, 4vw, 100px);
  width: auto;
  object-fit: contain;
}

.badge {
  background: #e8eefc;
  color: #3a5bdc;
  padding: clamp(2px, 0.5vw, 6px) clamp(6px, 1vw, 14px);
  font-size: clamp(13px, 0.7vw, 18px);
  border-radius: 20px;
}

.badge.light {
  background: #eef1f6;
  color: #5f6c7b;
}

.right {
  position: absolute;
  right: clamp(12px, 2vw, 28px);
  display: flex;
  gap: 16px;
  align-items: center;
  z-index: 1;
}

.counts {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
}

.user { 
  display:flex; 
  flex-direction:column; 
  font-size:clamp(14px, 1vw, 18px);
  transition: margin-left 0.3s ease-out;
}

.auth-actions {
  display: flex;
  gap: 8px;
}

.auth-btn:hover {
  background: #dfe7ff;
}

/* Language toggle button - match login button size */
.language-toggle {
  padding: 12px 20px !important;
  font-size: 19px !important;
  min-width: 100px !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 8px !important;
  color: #0f172a !important;
}
.language-toggle:hover {
  color: #0f172a !important;
}

/* Asetusrattaan tyylit ja animaatiot */
.login-btn {
  background: #1264a3;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 500;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
  font-size: 19px;
  min-width: 140px;
  flex-shrink: 0;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-btn:focus-visible {
  outline: 2px solid #0f5791;
  outline-offset: 2px;
}

.login-btn:hover {
  background: #0f5791;
  box-shadow: 0 2px 8px rgba(18, 100, 163, 0.3);
}

.login-btn:active {
  background: #0d4570;
}

/* Pudotusvalikon asemointi ja varjostus */
.menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
  z-index: 1001;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-item {
  border: none;
  background: transparent;
  text-align: left;
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: #0f172a;
}

.menu-item:hover {
  background: #f1f5f9;
}

.gear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  min-width: 48px;
  padding: 0;
  background: #ffffff;
  border: 2px solid #eef1f6;
  border-radius: 16px;
  color: #0f172a;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
  transition: all 0.2s ease;
}
.gear:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
  color: #0f172a;
}

.gear:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
  color: #475569;
}

.gear:focus-visible {
  outline: 2px solid #0f5791;
  outline-offset: 2px;
}

.login-toast {
  position: fixed;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  background: #dcfce7;
  color: #166534;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  z-index: 3000;
  animation: toastEnter 0.25s ease;
}

.toast-icon {
  font-size: 16px;
}

.toast-text {
  line-height: 1.2;
}

@keyframes toastEnter {
  from {
    opacity: 0;
    transform: translate(-50%, -10px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}
</style>
