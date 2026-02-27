<template>
  <div class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <button class="close-btn" @click="closeModal">&times;</button>
      <h2>{{ $t("settings.title") }}</h2>

      <div class="settings-container">
        <!-- Vasemman reunan valikko -->
        <div class="settings-menu">
          <ul>
            <li
              v-for="section in sections"
              :key="section.key"
              :class="{ active: activeSection === section.key }"
              @click="activeSection = section.key"
            >
              {{ $t(`settings.${section.key}`) }}
            </li>
          </ul>
        </div>

        <!-- Oikean reunan sisältö -->
        <div class="settings-content">
          <PersonalInfo v-if="activeSection === 'personalInfo'" />
          <ModifyPersonalInfo v-if="activeSection === 'modifyPersonalInfo'" />


          <UserLogin v-if="!auth.isAuthenticated && activeSection === 'login'" />
          <UserRegister
            v-if="!auth.isAuthenticated && activeSection === 'register'"
            @close="closeModal"
          />
          <AccessibilitySettings v-if="activeSection === 'accessibility'" />
          <AnalyticsInsights v-if="activeSection === 'analytics'" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { useAuthStore } from "@/stores/authStore";

import PersonalInfo from "./settings/PersonalInfo.vue";
import ModifyPersonalInfo from "./settings/ModifyPersonalInfo.vue";
import UserLogin from "./settings/UserLogin.vue";
import UserRegister from "./settings/UserRegister.vue";

const auth = useAuthStore();
const activeSection = ref("personalInfo");

// Props: määritä aloitusosio
const props = defineProps({
  initialSection: {
    type: String,
    default: "personalInfo",
  },
});

// Emit-tapahtuman määrittely
const emit = defineEmits(["close"]);

// Sulje modali
const closeModal = () => {
  emit("close");
};

const sections = computed(() => {
  const base = [{ key: "personalInfo" }, { key: "modifyPersonalInfo" }];

  if (!auth.isAuthenticated) {
    base.push({ key: "login" }, { key: "register" });
  }

  return base;
});


// Asetetaan aloitusosio, kun komponentti avataan
watch(
  () => props.initialSection,
  (newVal) => {
    if (auth.isAuthenticated && (newVal === "login" || newVal === "register")) {
      activeSection.value = "personalInfo";
    } else {
      activeSection.value = newVal;
    }
  },
  { immediate: true }
);

</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  background: white;
  padding: 24px;
  border-radius: 12px;
  width: 800px;
  height: 600px;
  max-width: 90%;
  max-height: 90%;
  box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #333;
}

h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.settings-container {
  display: flex;
  gap: 24px;
  flex: 1;
}

.settings-menu {
  width: 200px;
  border-right: 1px solid #e0e0e0;
  padding-right: 16px;
}

.settings-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.settings-menu li {
  padding: 12px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  border-radius: 8px;
  color: #666;
}

.settings-menu li:hover {
  background: #f5f5f5;
  color: #333;
}

.settings-menu li.active {
  background: #e0e0e0;
  color: #333;
  font-weight: bold;
}

.settings-content {
  flex: 1;
  padding: 8px;
}
</style>
