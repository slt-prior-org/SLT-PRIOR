<template>
  <div class="modern-settings">
    <div class="settings-header">
      <h2>{{ $t('modifyPersonalInfo.title') }}</h2>
      <p class="settings-subtitle">{{ $t('modifyPersonalInfo.healthInfo') }}</p>
    </div>

    <!-- Kirjautumisviesti (pelkkä teksti) -->
    <div v-if="!isLoggedIn" class="login-prompt">
      <p>{{ $t('personalInfo.loginPrompt') }}</p>
    </div>

    <template v-else>
      <form @submit.prevent="handleSubmit" class="modern-form">
        <div class="form-grid">
          <!-- Basic Info -->
          <div class="form-card">
            <h3 class="form-card-title">{{ $t('modifyPersonalInfo.basicInfo') }}</h3>
            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.weight') }}:</span>
                <div class="input-wrapper">
                  <input v-model="formData.weight" type="number" step="0.1" class="modern-input" />
                  <span class="input-unit">{{ $t('units.kg') }}</span>
                </div>
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.height') }}:</span>
                <div class="input-wrapper">
                  <input v-model="formData.height" type="number" step="0.1" class="modern-input" />
                  <span class="input-unit">{{ $t('units.cm') }}</span>
                </div>
              </label>
            </div>
          </div>

          <!-- Health Info -->
          <div class="form-card">
            <h3 class="form-card-title">{{ $t('modifyPersonalInfo.healthInfo') }}</h3>
            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.avgBloodPressure') }}:</span>
                <input v-model="formData.avg_blood_pressure" type="text" class="modern-input" placeholder="120/80" />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.alcoholUse') }}:</span>
                <select v-model="formData.alcohol_use" class="modern-input">
                  <option value="">{{ $t('options.none') }}</option>
                  <option value="occasional">{{ $t('options.occasional') }}</option>
                  <option value="moderate">{{ $t('options.moderate') }}</option>
                  <option value="heavy">{{ $t('options.heavy') }}</option>
                </select>
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.activity') }}:</span>
                <select v-model="formData.activity" class="modern-input">
                  <option value="">{{ $t('options.none') }}</option>
                  <option value="sedentary">{{ $t('options.sedentary') }}</option>
                  <option value="light">{{ $t('options.light') }}</option>
                  <option value="active">{{ $t('options.active') }}</option>
                  <option value="very_active">{{ $t('options.very_active') }}</option>
                </select>
              </label>
            </div>
          </div>

          <!-- Medical Info -->
          <div class="form-card">
            <h3 class="form-card-title">{{ $t('modifyPersonalInfo.medicalInfo') }}</h3>
            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.conditions') }}:</span>
                <input v-model="formData.conditions" type="text" class="modern-input" 
                      :placeholder="$t('patientForm.conditionsPlaceholder')" />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.riskFactors') }}:</span>
                <input v-model="formData.risk_factors" type="text" class="modern-input" 
                      :placeholder="$t('patientForm.riskFactorsPlaceholder')" />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.allergies') }}:</span>
                <input v-model="formData.allergies" type="text" class="modern-input" 
                      :placeholder="$t('patientForm.allergiesPlaceholder')" />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.medications') }}:</span>
                <input v-model="formData.medications" type="text" class="modern-input" 
                      :placeholder="$t('patientForm.medicationsPlaceholder')" />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t('personalInfo.heartProcedures') }}:</span>
                <input v-model="formData.heart_procedures" type="text" class="modern-input" 
                      :placeholder="$t('patientForm.heartProceduresPlaceholder')" />
              </label>
            </div>
          </div>
        </div>

        <button type="submit" class="modern-submit-btn">
          {{ $t('modifyPersonalInfo.save') }}
          <svg class="submit-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 12L10 17L20 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>

        <div v-if="message" :class="['modern-message', messageType === 'success' ? 'success' : 'error']">
          {{ message }}
        </div>
      </form>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';

const { t } = useI18n();

const isLoggedIn = ref(false);
const message = ref('');
const messageType = ref('');
const formData = ref({
  weight: '',
  height: '',
  avg_blood_pressure: '',
  alcohol_use: '',
  activity: '',
  conditions: '',
  risk_factors: '',
  allergies: '',
  medications: '',
  heart_procedures: ''
});

const userId = ref(null);

const checkLoginStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8000/api/users/check-session');
    isLoggedIn.value = response.data?.isLoggedIn || false;
    if (isLoggedIn.value) {
      userId.value = JSON.parse(localStorage.getItem('user'))?._id;
      loadUserData();
    }
  } catch (error) {
    console.error('Session check failed:', error);
    isLoggedIn.value = localStorage.getItem('isLoggedIn') === 'true';
    if (isLoggedIn.value) {
      userId.value = JSON.parse(localStorage.getItem('user'))?._id;
      loadUserData();
    }
  }
};

const loadUserData = () => {
  const user = JSON.parse(localStorage.getItem('user'));

  if (user) {
    formData.value.weight = user.weight || '';
    formData.value.height = user.height || '';
    formData.value.avg_blood_pressure = user.avg_blood_pressure || '';
    formData.value.alcohol_use = user.alcohol_use || '';
    formData.value.activity = user.activity || '';

    formData.value.conditions = (user.conditions || []).join(', ');
    formData.value.risk_factors = (user.risk_factors || []).join(', ');
    formData.value.allergies = (user.allergies || []).join(', ');
    formData.value.medications = (user.medications || []).join(', ');
    formData.value.heart_procedures = (user.heart_procedures || []).join(', ');
  }
};

onMounted(() => {
  checkLoginStatus();
});

const handleSubmit = async () => {
  if (!isLoggedIn.value) return;
  
  message.value = '';
  messageType.value = '';

  const payload = {
    ...formData.value,
    conditions: formData.value.conditions.split(',').map(s => s.trim()).filter(Boolean),
    risk_factors: formData.value.risk_factors.split(',').map(s => s.trim()).filter(Boolean),
    allergies: formData.value.allergies.split(',').map(s => s.trim()).filter(Boolean),
    medications: formData.value.medications.split(',').map(s => s.trim()).filter(Boolean),
    heart_procedures: formData.value.heart_procedures.split(',').map(s => s.trim()).filter(Boolean),
  };

  try {
    const response = await axios.put(
      `http://localhost:8000/api/users/id/${userId.value}`,
      payload,
      {
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json'
        }
      }
    );

    if (response.data.status === 'success') {
      message.value = t('modifyPersonalInfo.saveSuccess');
      messageType.value = 'success';

      localStorage.setItem('user', JSON.stringify(response.data.user));

      window.dispatchEvent(new CustomEvent('userDataUpdated', {
        detail: response.data.user
      }));
    } else {
      message.value = t(`modifyPersonalInfo.${response.data.message}`);
      messageType.value = 'error';
    }
  } catch (error) {
    const key = error.response?.data?.message || 'saveError';
    message.value = t(`modifyPersonalInfo.${key}`);
    messageType.value = 'error';
  }
};
</script>

<style scoped>
@import "@/assets/settingsstyles.css";

.login-prompt {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  text-align: center;
  color: #6c757d;
}

.login-prompt p {
  margin: 0;
}
</style>