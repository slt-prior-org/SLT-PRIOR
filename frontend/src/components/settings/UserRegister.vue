<template>
  <div class="settings-section">
    <h2>{{ $t("register.title") }}</h2>
    
    <div class="name-fields">
      <input
        type="text"
        v-model="firstName"
        :placeholder="t('register.firstName')"
      >
      <input
        type="text"
        v-model="lastName"
        :placeholder="t('register.lastName')"
      >
    </div>

    <input
      type="text"
      v-model="email"
      :placeholder="t('register.email')"
    >
    
    <div class="password-field">
      <input
        type="password"
        v-model="password"
        :placeholder="t('register.password')"
      >
    </div>

    <button @click="handleRegister">{{ $t("register.register") }}</button>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const firstName = ref('');
const lastName = ref('');
const email = ref('');
const password = ref('');

const { t } = useI18n();
const handleRegister = async () => {
};
</script>

<style scoped>

.login-message {
  margin-top: 1rem;
  font-size: 0.9rem;
  padding: 10px;
  border-radius: 4px;
}
.name-fields {
  display: flex;
  gap: 10px; /* space between the inputs */
  margin-bottom: 12px; /* space below inputs */
  margin-top: 12px; /* space above inputs */
}

.name-fields input {
  flex: 1; /* make both inputs take equal width */
}

.password-field {
  margin-top: 12px;  /* adds space above password input */
  margin-bottom: 12px; /* adds space below password input */
}

.password-field input {
  width: 100%;
  padding: 8px;
  font-size: 1rem;
  border-radius: 4px;
  border: 1px solid #ccc;
}

@import "@/assets/settingsstyles.css";
</style>