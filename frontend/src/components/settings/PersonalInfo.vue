<template>
  <div class="settings-section">
    <h2>{{ $t("personalInfo.title") }}</h2>

    <!-- Kirjautumisviesti (pelkkä teksti) -->
    <div v-if="!auth.isAuthenticated" class="login-prompt">
      <p>{{ $t("personalInfo.loginPrompt") }}</p>
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
          <span class="label">{{ $t("personalInfo.avgBloodPressure") }}: </span>
          <span class="value">
            {{ avgBpText }}
          </span>
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

<script setup>
import { onMounted, computed } from "vue";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();

onMounted(() => {
  // ensures we have fresh user data when opening settings
  auth.fetchUser();
});

const patient = computed(() => auth.user?.patient_info ?? {});

const avgBpText = computed(() => {
  const bp = patient.value?.avg_blood_pressure;
  if (!bp || (bp.systolic == null && bp.diastolic == null)) {
    return "—";
  }
  if (bp.systolic != null && bp.diastolic != null) return `${bp.systolic}/${bp.diastolic}`;
  if (bp.systolic != null) return `${bp.systolic}/—`;
  return `—/${bp.diastolic}`;
});

/* export default {
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
} */
</script>

<style scoped>
@import "@/assets/settingsstyles.css";
</style>