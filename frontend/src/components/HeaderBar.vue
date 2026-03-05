<template>
  <header class="header">
    <div class="header-left">
      <button
        class="sidebar-toggle"
        type="button"
        @click="handleSidebarToggle"
        aria-label="Toggle sidebar"
      >
        <FontAwesomeIcon :icon="isSidebarOpen ? 'times' : 'bars'" />
      </button>
    </div>

    <div class="header-center" aria-label="HeartWise logo">
      <img src="@/assets/logo.png" alt="HeartWise Logo" class="logo" />
    </div>

    <div class="header-right">
      <div class="language-selector">
        <select v-model="locale" @change="changeLanguage">
          <option value="fi">{{ $t("fin") }}</option>
          <option value="en">{{ $t("eng") }}</option>
        </select>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useI18n } from "vue-i18n";

defineProps({ isSidebarOpen: Boolean });

const emit = defineEmits(["toggle-sidebar"]);
const { locale } = useI18n();

const handleSidebarToggle = () => emit("toggle-sidebar");

const changeLanguage = (event) => {
  const newLocale = event.target.value;
  locale.value = newLocale;
  localStorage.setItem("selectedLanguage", newLocale);
};
</script>

<style scoped>
.header {
  position: sticky;
  top: 0;
  z-index: 50;

  height: 100px;
  min-height: 100px;
  flex: 0 0 100px;
  box-sizing: border-box;

  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;

  padding: 0 32px;
  background-color: #ffffff;
  border-bottom: 1px solid #dbeafe;
}

.header-left {
  justify-self: start;
  display: flex;
  align-items: center;
}

.header-center {
  justify-self: center;
  display: flex;
  align-items: center;
  justify-content: center;

  position: static;
  transform: none;
  pointer-events: none;
}

.header-right {
  justify-self: end;
  display: flex;
  align-items: center;
}

.sidebar-toggle {
  background: none;
  border: none;
  color: #0f172a;
  font-size: 30px;
  cursor: pointer;

  padding: 14px; 
  border-radius: 14px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* bigger logo */
.logo {
  height: 64px;
  width: auto;
  display: block;
  pointer-events: auto;
}

/* bigger language selector */
.language-selector select {
  height: 44px;       
  padding: 0 14px;  
  font-size: 16px;    
  background: #f8fafc;
  color: #0f172a;
  border: 1px solid #cbd5e1;
  border-radius: 12px; 
  cursor: pointer;
}

/* Responsive */
@media (max-width: 768px) {
  .header {
    height: 92px;
    min-height: 92px;
    flex: 0 0 92px;
    padding: 0 18px;
  }
  .logo {
    height: 68px;
  }
  .sidebar-toggle {
    font-size: 32px;
    padding: 14px;
  }
  .language-selector select {
    height: 46px;
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .header {
    height: 84px;
    min-height: 84px;
    flex: 0 0 84px;
    padding: 0 14px;
  }
  .logo {
    height: 60px;
  }
  .sidebar-toggle {
    font-size: 30px;
    padding: 12px;
  }
  .language-selector select {
    height: 44px;
    font-size: 15px;
    padding: 0 12px;
  }
}
</style>