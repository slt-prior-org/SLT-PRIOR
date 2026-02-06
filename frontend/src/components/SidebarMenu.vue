<template>
  <aside :class="['sidebar', { open: isOpen }]">
    <ul>
      <li><a href="#"><p>{{ $t("home") }}</p></a></li>
      <li>
        <a
          href="#"
          @click="settingsOpen = true"
        >{{ $t("settings.title") }}</a>
      </li>
      <li>
  <a href="#" @click.prevent="handleLoginLogout">
    <p>{{ loggedIn ? $t("logout") : $t("settings.login") }}</p>
  </a>
  </li>
  <li v-if="!loggedIn">
    <a href="#" @click.prevent="openRegisterForm">
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
import { defineProps, defineEmits, ref, onMounted } from "vue";
import SettingsModal from "./SettingsModal.vue";
import axios from "axios";

defineProps({ isOpen: Boolean });
const emit = defineEmits(["open-patient-form"]);

const loggedIn = ref(localStorage.getItem('isLoggedIn') === 'true');
const settingsOpen = ref(false);
const initialSettingsSection = ref("personalInfo");

// Reaktiivinen tila seuranta
onMounted(() => {
  window.addEventListener('authChange', () => {
    loggedIn.value = localStorage.getItem('isLoggedIn') === 'true';
  });
});

const openPatientForm = () => emit("open-patient-form");

const handleLoginLogout = async () => {
  if (loggedIn.value) {
    try {
      await axios.post('http://localhost:8000/users/logout');
      localStorage.removeItem('user');
      localStorage.setItem('isLoggedIn', 'false');
      loggedIn.value = false;
      window.dispatchEvent(new CustomEvent('authChange'));
      console.log("Uloskirjautuminen onnistui");
    } catch (error) {
      console.error("Uloskirjautumisvirhe:", error);
    }
  } else {
    settingsOpen.value = true;
    initialSettingsSection.value = "login";
  }
};

const openRegisterForm = () => {
  settingsOpen.value = true;
  initialSettingsSection.value = "register";
};


</script>


<style scoped>
.sidebar {
  position: fixed;
  top: 90px; /* Match header height */
  left: -250px;
  height: calc(100% - 90px); /* Adjust height to avoid overlapping header */
  background: var(--border-color);
  color: var(--text-light);
  padding: 30px 50px;
  transition: left 0.2s;
  font-size: 1rem;
  font-family: 'Arial', sans-serif; /* Sama fontti kuin chat-ikkunan nappuloissa */
}

/* Responsiivisuus eri näyttöleveydellä */
@media (max-width: 768px) {
  .sidebar {
    top: 80px;
    height: calc(100% - 80px);
  }
}

@media (max-width: 480px) {
  .sidebar {
    top: 70px;
    height: calc(100% - 70px);
  }
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
  font-size: 16px;
  font-family: 'Arial', sans-serif;
  transition: color 0.2s ease-in-out;
  cursor: pointer;
  padding: 8px 0;

}

a:hover {
  color: #005b96;
}

.sidebar.open {
  left: 0;
}


.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  display: block;
  margin-bottom: 10px;
}
</style>
