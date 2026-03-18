<script setup>
import { computed, ref } from "vue"
import { useI18n } from "vue-i18n"
import SettingsModal from "./SettingsModal.vue"
import AppButton from "@/components/ui/AppButton.vue"
import { useAuthStore } from "@/stores/authStore"

// Komponentin ottamat vastaanottamat tiedot
defineProps({
  queueCount: Number,
  closedCount: Number,
  user: Object,
  showLanguageSwitcher: {
    type: Boolean,
    default: true
  },
  showCounts: {
    type: Boolean,
    default: false
  }
})

// Alustetaan kielituki ja käyttäjästore
const auth = useAuthStore()
const i18n = useI18n()

// Tarkistetaan onko käyttäjä kirjautunut sisään
const loggedIn = computed(() => !!auth.user)

// Funktio sovelluksen kielen vaihtamiseen
function switchLanguage(lang) {
  i18n.locale.value = lang
}

// Valikkojen ja modaalien näkyvyyden hallinta
const menuOpen = ref(false)
const settingsOpen = ref(false)
const initialSettingsSection = ref("personalInfo")

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

// Funktio asetusikkunan avaamiseen tietystä osiosta
function openSettings(section) {
  settingsOpen.value = true
  initialSettingsSection.value = section
  menuOpen.value = false
}

// Lasketaan pudotusvalikon kohteet kirjautumistilan mukaan
const dropdownItems = computed(() => {
  if (loggedIn.value) {
    return [
      { key: "settings", labelKey: "settings.title", action: () => openSettings("personalInfo") },
      { key: "logout", labelKey: "logout", action: () => handleLoginLogout() },
    ]
  }

  return [
    { key: "settings", labelKey: "settings.title", action: () => openSettings("personalInfo") },
    { key: "login", labelKey: "settings.login", action: () => openSettings("login") },
    { key: "register", labelKey: "settings.register", action: () => openSettings("register") }
  ]
})

// Uloskirjautumisen tai kirjautumissivun avaamisen hallinta
async function handleLoginLogout() {
  if (loggedIn.value) {
    try {
      await auth.logout()
    } catch (error) {
      console.error("Uloskirjautumisvirhe:", error)
    }
  } else {
    openSettings("login")
  }

  menuOpen.value = false
}
</script>

<template>
  <div class="header" :class="{ disabled: settingsOpen }">

    <div class="left">
      <div v-if="loggedIn" class="user">
        <strong>{{ user?.name || "" }}</strong>
        <small>{{ user?.role || "" }}</small>
      </div>
    </div>

    <div class="center">
      <img src="@/assets/new_logo.png" alt="HeartWise Logo" class="logo" />
    </div>

    <div class="right">

      <div v-if="showCounts" class="counts">
        <span class="badge">
          JONOSSA {{ queueCount }}
        </span>
        <span class="badge light">
          VALMIS {{ closedCount }}
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

      <AppButton class="gear" variant="neutral" @click="toggleMenu">
        <svg
          viewBox="0 0 24 24"
          width="22"
          height="22"
          aria-hidden="true"
        >
          <path
            d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Zm8 3.5a7.9 7.9 0 0 0-.08-1.12l2.04-1.59-2-3.46-2.46.98a8.15 8.15 0 0 0-1.94-1.13L15.2 2h-4.4l-.36 2.81a8.15 8.15 0 0 0-1.94 1.13l-2.46-.98-2 3.46 2.04 1.59A7.9 7.9 0 0 0 6 12c0 .38.03.75.08 1.12l-2.04 1.59 2 3.46 2.46-.98c.6.48 1.25.86 1.94 1.13L10.8 22h4.4l.36-2.81a8.15 8.15 0 0 0 1.94-1.13l2.46.98 2-3.46-2.04-1.59c.05-.37.08-.74.08-1.12Z"
            fill="currentColor"
          />
        </svg>
      </AppButton>

      <div v-if="menuOpen" class="menu">
        <AppButton
          v-for="item in dropdownItems"
          :key="item.key"
          class="menu-item"
          variant="neutral"
          @click="item.action()"
        >
          {{ $t(item.labelKey) }}
        </AppButton>
      </div>
    </div>

  </div>

  <div
    v-if="menuOpen"
    class="menu-backdrop"
    @click="menuOpen = false"
  />

  <SettingsModal
    v-if="settingsOpen"
    :initialSection="initialSettingsSection"
    @close="settingsOpen = false"
  />
</template>

<style scoped>
/* Yläpalkin asemointi ja ulkoasu */
.header {
  position: relative;
  display:flex;
  justify-content:center;
  align-items:center;
  padding:16px 28px;
  background:white;
  border-bottom:1px solid #eee;
  z-index: 1002;
  transition: opacity 0.2s;
}

.header.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.left {
  position: absolute;
  left: 28px;
  display:flex; 
  align-items:center;
}
.center { 
  display:flex; 
  gap:12px; 
  align-items:center; 
}

.logo {
  width: 200px;
  height: 100px;
  object-fit: contain;
}

.badge {
  background:#e8eefc;
  color:#3a5bdc;
  padding:6px 14px;
  border-radius:20px;
}

.badge.light {
  background:#eef1f6;
  color:#5f6c7b;
}

.right {
  position: absolute;
  right: 28px;
  display:flex;
  gap:16px;
  align-items:center;
  z-index: 1;
}

.user { display:flex; flex-direction:column; font-size:18px; }

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
.gear {
  background:#eef2f8;
  border:none;
  border-radius:22px;
  min-width:44px;
  min-height:44px;
  padding:10px;
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  transition: background 0.2s, transform 0.15s;
}

.gear:hover {
  background:#dfe7ff;
}

.gear:active {
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
</style>