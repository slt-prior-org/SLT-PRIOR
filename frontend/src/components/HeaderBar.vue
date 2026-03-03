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
  position: sticky;
  top: 0;
  z-index: 50;

  /* lukitus ettei enää kutistu */
  height: 64px;
  min-height: 64px;
  flex: 0 0 64px;
  box-sizing: border-box;

  /* layout */
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;

  padding: 0 25px;
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

  /* tärkeää: ei absolute-keskitystä */
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
  font-size: 24px;
  cursor: pointer;

  /* pidä nappi keskellä headeria */
  padding: 10px;
  border-radius: 12px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.logo {
  height: 50px;
  width: auto;
  display: block;       
  pointer-events: auto; 
}

.language-selector select {
  height: 36px;         /* tekee siitä tasakorkuisen */
  padding: 0 10px;
  font-size: 14px;
  background: #f8fafc;
  color: #0f172a;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  cursor: pointer;
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