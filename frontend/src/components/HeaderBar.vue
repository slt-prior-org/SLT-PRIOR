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
      <img src="@/assets/logo.png" alt="HeartWise Logo" class="logo">
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
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;

  height: 90px;
  padding: 0 25px;

  background-color: #ffffff;
  border-bottom: 1px solid #dbeafe;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  z-index: 2; 
}

.sidebar-toggle {
  background: none;
  border: none;
  color: #0f172a;
  font-size: 24px;
  cursor: pointer;
  padding: 15px;
  border-radius: 12px;
}
.sidebar-toggle:hover {
  background: #f1f5f9;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1;

  display: flex;
  align-items: center;
  justify-content: center;

  pointer-events: none; 
}
.logo {
  height: 64px;
  width: auto;
  pointer-events: auto;
}

.language-selector select {
  padding: 8px 10px;
  font-size: 14px;
  background: #f8fafc;
  color: #0f172a;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  cursor: pointer;
}
.language-selector select:focus {
  border-color: #1d4ed8;
  outline: none;
}

/* Responsive */
@media (max-width: 768px) {
  .header {
    height: 80px;
    padding: 0 16px;
  }
  .logo {
    height: 56px;
  }
}

@media (max-width: 480px) {
  .header {
    height: 70px;
    padding: 0 12px;
  }
  .logo {
    height: 50px;
  }
  .language-selector select {
    font-size: 12px;
    padding: 7px 8px;
  }
}
</style>