<template>
  <div class="layout">
    <HeaderBar
      :queue-count="queueCount"
      :closed-count="closedCount"
    />
    <main>
      <Chat
        :external-show-form="showForm"
        @update:external-show-form="showForm = $event"
        @open-login="openSettings('login')"
        @open-register="openSettings('register')"
      />
    </main>
  </div>
</template>
  
<script setup>
import { ref } from "vue";
import HeaderBar from "@/components/ui/HeaderBar.vue";
import Chat from "@/components/chat/Chat.vue";

// Lomakkeen näkyvyyden tila
const showForm = ref(false);
// Vakioarvot jonojen laskureille (voidaan dynaamistaa myöhemmin)
const queueCount = 0;
const closedCount = 0;

// Modalin tilan hallinta
const settingsOpen = ref(false);
const initialSettingsSection = ref("personalInfo");

// TÄMÄ FUNKTIO PUUTTUI TAI OLI VIRHEELLINEN
const openSettings = (section) => {
  console.log("Availlaan osiota:", section); // Lisää tämä testiksi konsoliin
  initialSettingsSection.value = section;
  settingsOpen.value = true;
};
</script>
  
<style scoped>
/* Koko näytön korkuinen asettelu pystysuunnassa */
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* Chat-alue täyttää kaiken jäljelle jäävän tilan */
main {
  flex: 1 1 auto;
  min-height: 0;
}
</style>