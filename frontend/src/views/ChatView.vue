<template>
  <div class="layout">
    <HeaderBar
      :queue-count="queueCount"
      :closed-count="closedCount"
      :user="headerUser"
      @open-patient-form="openPatientForm"
    />
    <main>
      <Chat
        :external-show-form="showForm"
        @update:external-show-form="showForm = $event"
      />
    </main>
  </div>
</template>
  
<script setup>
import { computed, ref } from "vue";
import { storeToRefs } from "pinia";
import HeaderBar from "@/components/HeaderBar.vue";
import Chat from "@/components/Chat.vue";
import { useAuthStore } from "@/stores/authStore";

// Lomakkeen näkyvyyden tila
const showForm = ref(false);
// Vakioarvot jonojen laskureille (voidaan dynaamistaa myöhemmin)
const queueCount = 0;
const closedCount = 0;

// Haetaan käyttäjätiedot keskitetystä storesta reaktiivisesti
const authStore = useAuthStore();
const { user } = storeToRefs(authStore);

// Muotoillaan käyttäjän nimi ja rooli HeaderBar-komponentille sopivaksi
const headerUser = computed(() => {
  const currentUser = user.value;
  if (!currentUser) return { name: "...", role: "" };

  // Yhdistetään etu- ja sukunimi, jos ne löytyvät
  const fullName = [currentUser.first_name, currentUser.last_name]
    .filter(Boolean)
    .join(" ")
    .trim();

  return {
    name: fullName || currentUser.name || currentUser.email || "...",
    role: currentUser.role || "",
  };
});

// Funktio potilaslomakkeen avaamiseksi
const openPatientForm = () => {
  showForm.value = true;
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