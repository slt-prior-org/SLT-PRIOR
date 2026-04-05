<template>
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

  <div class="header">
    <div class="left">
      <div v-if="loggedIn" class="user">
        <strong>{{ fullName }}</strong>
        <small>{{ user?.role || "" }}</small>
      </div>
    </div>

    <div class="center">
      <img src="@/assets/new_logo.png" alt="HeartWise Logo" class="logo" />
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

      <div v-if="showLanguageSwitcher" class="language-switcher">
        <AppButton
          :class="{ active: i18n.locale.value === 'en' }"
          variant="neutral"
          @click="switchLanguage('en')"
        >
          EN
        </AppButton>
        <AppButton
          :class="{ active: i18n.locale.value === 'fi' }"
          variant="neutral"
          @click="switchLanguage('fi')"
        >
          FI
        </AppButton>
      </div>

      <AppButton
        v-if="loggedIn"
        class="gear"
        variant="neutral"
        @click="toggleMenu"
      >
        <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
          <path
            d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm8 3.5a7.9 7.9 0 0 0-.08-1.12l2.04-1.59-2-3.46-2.46.98a8.15 8.15 0 0 0-1.94-1.13L15.2 2h-4.4l-.36 2.81a8.15 8.15 0 0 0-1.94 1.13l-2.46-.98-2 3.46 2.04 1.59A7.9 7.9 0 0 0 6 12c0 .38.03.75.08 1.12l-2.04 1.59 2 3.46 2.46-.98c.6.48 1.25.86 1.94 1.13L10.8 22h4.4l.36-2.81a8.15 8.15 0 0 0 1.94-1.13l2.46.98 2-3.46-2.04-1.59c.05-.37.08-.74.08-1.12Z"
            fill="currentColor"
          />
        </svg>
      </AppButton>

      <AppButton
        v-else
        class="login-btn"
        size="lg"
        variant="primary"
        @click="openAuthModal('login')"
      >
        {{ $t("settings.login") }}
      </AppButton>

      <SettingsDropdownMenu
        v-if="menuOpen"
        :items="dropdownItems"
        @close="menuOpen = false"
      />
    </div>
  </div>

  <div v-if="menuOpen" class="menu-backdrop" @click="menuOpen = false" />

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
  showLanguageSwitcher: {
    type: Boolean,
    default: true,
  },
  showCounts: {
    type: Boolean,
    default: false,
  },
})

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
const showAuth = ref(false)
const user = computed(() => auth.user)

// Yhdistetään etu- ja sukunimi, jos ne löytyvät
const fullName = computed(() => {
  const u = user.value
  if (!u) return ""

  const name = [u.first_name, u.last_name].filter(Boolean).join(" ").trim()

  return name || u.name || u.email || "..."
})

// Funktio sovelluksen kielen vaihtamiseen
function switchLanguage(lang) {
  i18n.locale.value = lang
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
  return [
    {
      key: "edit-health-profile",
      labelKey: "settings.editHealthProfile",
      action: () => openHealthProfile(),
    },
    {
      key: "logout",
      labelKey: "logout",
      action: handleLogout,
    },
  ]
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
  display: flex;
  align-items: center;
}
.center {
  display: flex;
  gap: 12px;
  align-items: center;
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

.user {
  display: flex;
  flex-direction: column;
  font-size: clamp(14px, 1vw, 18px);
}

.auth-actions {
  display: flex;
  gap: 8px;
}

.auth-btn:hover {
  background: #dfe7ff;
}

/* Kielivalitsimen painikkeiden tyylit */
.language-switcher {
  display: flex;
  gap: 4px;
}

.language-switcher button {
  font-weight: 600;
  border-radius: 6px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.language-switcher button.active {
  background: #3a5bdc;
  color: white;
  border-color: #3a5bdc;
}

.language-switcher button:hover:not(.active) {
  background: #f5f5f5;
}

/* Asetusrattaan tyylit ja animaatiot */
.login-btn {
  background: #3a5bdc;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  padding: 10px 18px;
  cursor: pointer;
  transition:
    background 0.2s,
    transform 0.15s;
}

.login-btn:hover {
  background: #2a45b8;
}

.login-btn:active {
  transform: scale(0.97);
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

/* Taustan himmennys valikon ollessa auki */
.menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
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
