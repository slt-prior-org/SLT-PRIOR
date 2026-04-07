<template>
  <div class="layout">
    <HeaderBar
      :queue-count="queueCount"
      :closed-count="closedCount"
      :sidebar-open="sidebarOpen && isAuthenticated && isPatient"
      @sidebar-toggle="toggleSidebar"
    />
    <div class="main-content">
      <Transition name="sidebar-fade">
        <ChatHistorySidebar
          v-if="sidebarOpen && isAuthenticated && isPatient"
          :chat-history="chatStore.getUserChats"
          :active-chat-id="chatStore.getActiveChat?.id"
          @select-chat="handleSelectChat"
          @start-new-chat="handleStartNewChat"
          @close-sidebar="sidebarOpen = false"
        />
      </Transition>
      <main>
        <Chat
          :external-show-form="showForm"
          @update:external-show-form="showForm = $event"
          @trigger-auth-modal="openAuthModal"
          @open-login="openSettings('login')"
          @open-register="openSettings('register')"
        />
        <AuthModal
          :show="showAuthModal"
          :initial-tab="activeAuthTab"
          @close="showAuthModal = false"
        />
      </main>
    </div>
  </div>
</template>
  
<script setup>
import { ref, onMounted, computed, watch } from "vue";
import HeaderBar from "@/components/ui/HeaderBar.vue";
import Chat from "@/components/chat/Chat.vue";
import AuthModal from "@/components/auth/AuthModal.vue";
import ChatHistorySidebar from "@/components/ChatHistorySidebar.vue";
import { useUserChatStore } from "@/stores/userChatStore";
import { useAuthStore } from "@/stores/authStore";

const showForm = ref(false);
const queueCount = 0;
const closedCount = 0;

const showAuthModal = ref(false);
const activeAuthTab = ref("login");

function openAuthModal(tab = "login") {
  activeAuthTab.value = tab;
  showAuthModal.value = true;
}
const settingsOpen = ref(false);
const initialSettingsSection = ref("personalInfo");
const chatStore = useUserChatStore();
const authStore = useAuthStore();
const isAuthenticated = computed(() => authStore.isAuthenticated);
const isPatient = computed(() => authStore.isPatient);
const sidebarOpen = ref(isAuthenticated.value); // oletuksena auki kirjautuneelle

const openSettings = (section) => {
  initialSettingsSection.value = section;
  settingsOpen.value = true;
};


const handleSelectChat = async (chat) => {
  if (chat && chat.id) {
    sidebarOpen.value = true;
    await chatStore.setActiveChat(chat.id);
  }
};


const handleStartNewChat = async () => {
  // Prevent starting a new chat only if the current chat is a draft (not yet saved)
  const currentChat = chatStore.activeChat;
  if (currentChat && currentChat.isDraft) {
    return;
  }
  sidebarOpen.value = true;
  chatStore.createDraftChat();
};

// Hallinnoi sidebarin avaamista / sulkemista
function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value;
}

onMounted(async () => {
  if (isAuthenticated.value) {
    await chatStore.initializeChats();
    await chatStore.loadChatsWithMessages();
  }
});

watch(isAuthenticated, async (newVal) => {
  if (newVal) {
    await chatStore.initializeChats();
    await chatStore.loadChatsWithMessages();
    sidebarOpen.value = true;
  } else {
    sidebarOpen.value = false;
  }
});
</script>
  
<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.main-content {
  display: flex;
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
}

main {
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
}

.sidebar-fade-leave-active {
  transition: opacity 0.3s ease-in, transform 0.3s ease-in;
}

.sidebar-fade-leave-to {
  opacity: 0;
  transform: translateX(-100%);
}
</style>