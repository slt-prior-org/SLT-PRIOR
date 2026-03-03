<template>
  <div class="layout" :class="{ 'sidebar-open': isSidebarOpen }">
    <HeaderBar
      :is-sidebar-open="isSidebarOpen"
      @toggle-sidebar="handleSidebarToggle"
    />
    <SidebarMenu
      :is-open="isSidebarOpen"
      @toggle-sidebar="handleSidebarToggle"
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
import { ref } from "vue";
import HeaderBar from "@/components/HeaderBar.vue";
import SidebarMenu from "@/components/SidebarMenu.vue";
import Chat from "@/components/Chat.vue";

const isSidebarOpen = ref(false);
const showForm = ref(false);

const handleSidebarToggle = () => {
  isSidebarOpen.value = !isSidebarOpen.value;
};

const openPatientForm = () => {
  showForm.value = true;
};
</script>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

main {
  flex: 1 1 auto;
  min-height: 0;

  display: flex;
  justify-content: center;
  align-items: stretch;

  /* remove this - it creates the visible gap */
  padding: 0;
}

/* Keep some outer padding only when sidebar is closed */
.layout:not(.sidebar-open) main {
  padding: 20px;
}

/* When sidebar is open, start content immediately next to it */
.layout.sidebar-open main {
  padding-left: 260px; /* must match SidebarMenu width */
  padding-right: 20px;
  padding-top: 20px;
  padding-bottom: 20px;
}
</style>