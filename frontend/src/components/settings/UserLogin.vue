<template>
  <div class="settings-section">
    <h2>{{ $t("login.title") }}</h2>

    <input
      type="email"
      v-model="email"
      :placeholder="t('login.email')"
      @keyup.enter="handleLogin"
    >

    <input
      type="password"
      v-model="password"
      :placeholder="t('login.password')"
      @keyup.enter="handleLogin"
    >

    <AppButton variant="primary" @click="handleLogin">{{ $t("login.logIn") }}</AppButton>

    <div
      v-if="loginMessage"
      :class="[
        'login-message',
        messageType === 'error' ? 'error-message' : 'success-message'
      ]"
    >
      {{ loginMessage }}
    </div>
  </div>
</template>

<script setup>

import { ref } from "vue";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/authStore";
import AppButton from "@/components/ui/AppButton.vue";
import { useRouter } from "vue-router";


const { t } = useI18n();
const auth = useAuthStore();
const router = useRouter();


const email = ref('')
const password = ref('')
const loginMessage = ref('')
const messageType = ref('')


// Kirjautumiskäsittelijä: lähettää tunnukset, näyttää viestin ja ohjaa roolin mukaan
const handleLogin = async () => {
  try {
    loginMessage.value = "";
    await auth.login(email.value, password.value);

    // Onnistunut kirjautuminen
    messageType.value = "success";
    loginMessage.value = t("loginStatus.success");

    // Ohjataan käyttäjä roolin perusteella oikealle sivulle
    if (auth.user?.role === "professional") {
      router.push("/professional");
    } else {
      router.push("/");
    }
  } catch (error) {
    // Virhe kirjautumisessa, näytetään viesti
    messageType.value = "error";
    const detail = error?.response?.data?.detail || "server_error";
    loginMessage.value = typeof detail === "string" ? detail : t("loginStatus.failed");
  } finally {
    setTimeout(() => (loginMessage.value = ""), 5000);
  }
};
</script>

<style scoped>

.login-message {
  margin-top: 1rem;
  font-size: 0.9rem;
  padding: 10px;
  border-radius: 4px;
}
@import "@/assets/settingsstyles.css";
</style>