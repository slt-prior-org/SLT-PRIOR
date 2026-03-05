<template>
  <aside :class="['sidebar', { open: isOpen }]">
    <ul>
      <li>
        <a href="#"><p>{{ $t("home") }}</p></a>
      </li>

      <li>
        <a href="#" @click.prevent="openSettings('personalInfo')">
          {{ $t("settings.title") }}
        </a>
      </li>

      <li>
        <a href="#" @click.prevent="handleLoginLogout">
          <p>{{ loggedIn ? $t("logout") : $t("settings.login") }}</p>
        </a>
      </li>

      <li v-if="!loggedIn">
        <a href="#" @click.prevent="openSettings('register')">
          <p>{{ $t("settings.register") }}</p>
        </a>
      </li>

      <li v-if="!loggedIn">
        <a href="#" @click.prevent="openPatientForm">
          <p>{{ $t("preliminaryForm") }}</p>
        </a>
      </li>
    </ul>
  </aside>

  <!-- Asetukset-modali -->
  <SettingsModal
    v-if="settingsOpen"
    @close="settingsOpen = false"
    :initialSection="initialSettingsSection"
  />
</template>

<script setup>
import { ref, computed } from "vue";
import SettingsModal from "./SettingsModal.vue";
import { useAuthStore } from "@/stores/authStore";

defineProps({ isOpen: Boolean });

const emit = defineEmits(["open-patient-form"]);

const auth = useAuthStore();
const loggedIn = computed(() => auth.isAuthenticated);

const settingsOpen = ref(false);
const initialSettingsSection = ref("personalInfo");

const openPatientForm = () => emit("open-patient-form");

const openSettings = (section) => {
  settingsOpen.value = true;
  initialSettingsSection.value = section;
};

const handleLoginLogout = async () => {
  if (loggedIn.value) {
    try {
      await auth.logout();
      console.log("Uloskirjautuminen onnistui");
    } catch (error) {
      console.error("Uloskirjautumisvirhe:", error);
    }
  } else {
    openSettings("login");
  }
};
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: -260px;
  width: 260px;
  top: 84px;         
  bottom: 0;         
  background: #0f172a;
  color: #fff;
  padding: 26px 22px;
  transition: left 0.2s;
  font-size: 1rem;
  font-family: Arial, sans-serif;
  z-index: 30;
  border-right: 1px solid rgba(255, 255, 255, 0.08);

  overflow-y: auto;
}
.sidebar.open {
  left: 0;
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

a {
  color: white;
  text-decoration: none;
  font-size: 15px;
  transition: color 0.2s ease-in-out, background-color 0.2s ease-in-out;
  cursor: pointer;
  padding: 10px 10px;
  border-radius: 10px;
  display: block;
}

a:hover {
  color: #93c5fd;
  background: rgba(255, 255, 255, 0.06);
}

/* Responsive */
@media (max-width: 768px) {
  .sidebar {
    top: 80px;
  }
}

@media (max-width: 480px) {
  .sidebar {
    top: 70px;
  }
}
</style>