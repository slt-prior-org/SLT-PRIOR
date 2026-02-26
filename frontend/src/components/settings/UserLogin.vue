<template>
  <div class="settings-section">
    <h2>{{ $t("login.title") }}</h2>
    <input
      type="text"
      v-model="userID"
      :placeholder="t('login.username')"
      @keyup.enter="handleLogin"
    >
    <button @click="handleLogin">{{ $t("login.logIn") }}</button>
    
    <!-- Yhdistetty viestialue -->
    <div 
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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';

const { t } = useI18n();
const userID = ref('');
const loginMessage = ref('');
const messageType = ref('');

const handleLogin = async () => {
  try {
    loginMessage.value = '';
    const response = await axios.post(
      'http://localhost:8000/api/users/login',
      { user_id: userID.value },
      {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      }
    );

    if (response.data.status === 'success') {
      // Lisätyt rivit kirjautumistilan hallintaan
      localStorage.setItem('isLoggedIn', 'true');
      window.dispatchEvent(new CustomEvent('authChange'));
      
      messageType.value = 'success';
      loginMessage.value = t('loginStatus.success');
      localStorage.setItem('user', JSON.stringify(response.data.user));
      window.location.href = '/#';
    } else {
      messageType.value = 'error';
      loginMessage.value = t(`loginStatus.${response.data.message}`);
    }

  } catch (error) {
    messageType.value = 'error';
    const errorKey = error.response?.data?.message || 'server_error';
    loginMessage.value = t(`loginStatus.${errorKey}`);
  } finally {
    setTimeout(() => {
      loginMessage.value = '';
    }, 5000);
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