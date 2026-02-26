<template>
  <div class="settings-section">
    <h2>{{ $t("personalInfo.title") }}</h2>

    <!-- Kirjautumisviesti (pelkkä teksti) -->
    <div v-if="!isLoggedIn" class="login-prompt">
      <p>{{ $t('personalInfo.loginPrompt') }}</p>
    </div>

    <!-- Käyttäjätiedot -->
    <template v-else>
      <!-- Perustiedot -->
      <div class="info-section">
        <h3>{{ $t('personalInfo.basicInfo') }}</h3>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.weight') }}: </span>
          <span class="value">{{ userData?.weight || $t('personalInfo.notProvided') }} {{ $t('units.kg') }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.height') }}: </span>
          <span class="value">{{ userData?.height || $t('personalInfo.notProvided') }} {{ $t('units.cm') }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.avgBloodPressure') }}: </span>
          <span class="value">{{ userData?.avg_blood_pressure || $t('personalInfo.notProvided') }}</span>
        </div>
      </div>

      <!-- Terveystiedot -->
      <div class="info-section">
        <h3>{{ $t('personalInfo.healthInfo') }}</h3>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.alcoholUse') }}: </span>
          <span class="value">{{ userData?.alcohol_use || $t('personalInfo.notProvided') }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.activity') }}: </span>
          <span class="value">{{ userData?.activity || $t('personalInfo.notProvided') }}</span>
        </div>
      </div>

      <!-- Lääketiedot -->
      <div class="info-section">
        <h3>{{ $t('personalInfo.medicalInfo') }}</h3>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.conditions') }}: </span>
          <ul v-if="userData?.conditions?.length" class="value-list">
            <li v-for="condition in userData.conditions" :key="condition">{{ condition }}</li>
          </ul>
          <span v-else class="value">{{ $t('personalInfo.notProvided') }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.riskFactors') }}: </span>
          <ul v-if="userData?.risk_factors?.length" class="value-list">
            <li v-for="factor in userData.risk_factors" :key="factor">{{ factor }}</li>
          </ul>
          <span v-else class="value">{{ $t('personalInfo.notProvided') }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.allergies') }}: </span>
          <ul v-if="userData?.allergies?.length" class="value-list">
            <li v-for="allergy in userData.allergies" :key="allergy">{{ allergy }}</li>
          </ul>
          <span v-else class="value">{{ $t('personalInfo.notProvided') }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.medications') }}: </span>
          <ul v-if="userData?.medications?.length" class="value-list">
            <li v-for="medication in userData.medications" :key="medication">{{ medication }}</li>
          </ul>
          <span v-else class="value">{{ $t('personalInfo.notProvided') }}</span>
        </div>
        <div class="info-row">
          <span class="label">{{ $t('personalInfo.heartProcedures') }}: </span>
          <ul v-if="userData?.heart_procedures?.length" class="value-list">
            <li v-for="procedure in userData.heart_procedures" :key="procedure">{{ procedure }}</li>
          </ul>
          <span v-else class="value">{{ $t('personalInfo.notProvided') }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'PersonalInfo',
  data() {
    return {
      userData: null,
      isLoggedIn: false
    }
  },
  async created() {
    await this.checkLoginStatus();
    if (this.isLoggedIn) {
      await this.fetchUserData();
    }
  },
  methods: {
    async checkLoginStatus() {
      try {
        const response = await axios.get('http://localhost:8000/api/users/check-session');
        this.isLoggedIn = response.data?.isLoggedIn || false;
      } catch (error) {
        console.error('Session check failed:', error);
        this.isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      }
    },
    async fetchUserData() {
      try {
        const response = await axios.get('http://localhost:8000/api/users/current-user');
        if (response.data.status === 'success') {
          this.userData = response.data.user;
        }
      } catch (error) {
        console.error('Failed to fetch user data:', error);
      }
    }
  }
}
</script>

<style scoped>
@import "@/assets/settingsstyles.css";
</style>