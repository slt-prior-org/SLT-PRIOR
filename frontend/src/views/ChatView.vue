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
        @trigger-auth-modal="openAuthModal"
      />
      <AuthModal
        :show="showAuthModal"
        :initial-tab="activeAuthTab"
        @close="showAuthModal = false"
      />
    </main>
  </div>
</template>
  
<script setup>
import { ref } from "vue";
import HeaderBar from "@/components/ui/HeaderBar.vue";
import Chat from "@/components/chat/Chat.vue";
import AuthModal from "@/components/auth/AuthModal.vue";

const showForm = ref(false);
const queueCount = 0;
const closedCount = 0;

const showAuthModal = ref(false);
const activeAuthTab = ref("login");

function openAuthModal(tab = "login") {
  activeAuthTab.value = tab;
  showAuthModal.value = true;
}
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