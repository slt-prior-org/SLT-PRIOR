<template>
  <div class="modern-settings">
    <div class="settings-header">
      <h2>{{ $t("modifyPersonalInfo.title") }}</h2>
      <p class="settings-subtitle">{{ $t("modifyPersonalInfo.healthInfo") }}</p>
    </div>

    <div v-if="!auth.isAuthenticated" class="login-prompt">
      <p>{{ $t("personalInfo.loginPrompt") }}</p>
    </div>

    <template v-else>
      <form @submit.prevent="handleSubmit" class="modern-form">
        <div class="form-grid">
          <div class="form-card">
            <h3 class="form-card-title">{{ $t("modifyPersonalInfo.basicInfo") }}</h3>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.weight") }}:</span>
                <div class="input-wrapper">
                  <input v-model="formData.weight" type="number" step="0.1" class="modern-input" />
                  <span class="input-unit">{{ $t("units.kg") }}</span>
                </div>
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.height") }}:</span>
                <div class="input-wrapper">
                  <input v-model="formData.height" type="number" step="0.1" class="modern-input" />
                  <span class="input-unit">{{ $t("units.cm") }}</span>
                </div>
              </label>
            </div>
          </div>

          <div class="form-card">
            <h3 class="form-card-title">{{ $t("modifyPersonalInfo.healthInfo") }}</h3>
            <label class="input-label">
              <span>{{ $t("personalInfo.bloodPressure") }}:</span>
                <div class="bp-inputs">
                  <span>{{ $t("personalInfo.systolic") }}:</span>
                  <input
                    v-model="formData.bp_systolic"
                    type="number"
                    min="50"
                    max="300"
                    class="modern-input"
                    placeholder="120"
                  />

                  <span>{{ $t("personalInfo.diastolic") }}:</span>

                  <input
                    v-model="formData.bp_diastolic"
                    type="number"
                    min="30"
                    max="200"
                    class="modern-input"
                    placeholder="80"
                  />
                </div>
            </label>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.alcoholUse") }}:</span>
                <select v-model="formData.alcohol_use" class="modern-input">
                  <option value="none">{{ $t("patientForm.alcoholNone") }}</option>
                  <option value="rare">{{ $t("patientForm.alcoholRare") }}</option>
                  <option value="monthly">{{ $t("patientForm.alcoholMonthly") }}</option>
                  <option value="weekly">{{ $t("patientForm.alcoholWeekly") }}</option>
                  <option value="daily">{{ $t("patientForm.alcoholDaily") }}</option>
                </select>
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.activity") }}:</span>
                <select v-model="formData.activity" class="modern-input">
                  <option value="none">{{ $t("options.none") }}</option>
                  <option value="sedentary">{{ $t("options.sedentary") }}</option>
                  <option value="light">{{ $t("patientForm.activityLight") }}</option>
                  <option value="moderate">{{ $t("patientForm.activityModerate") }}</option>
                  <option value="vigorous">{{ $t("patientForm.activityActive") }}</option>
                </select>
              </label>
            </div>
          </div>

          <div class="form-card">
            <h3 class="form-card-title">{{ $t("modifyPersonalInfo.medicalInfo") }}</h3>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.conditions") }}:</span>
                <input
                  v-model="formData.conditions"
                  type="text"
                  class="modern-input"
                  :placeholder="$t('patientForm.conditionsPlaceholder')"
                />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.riskFactors") }}:</span>
                <input
                  v-model="formData.risk_factors"
                  type="text"
                  class="modern-input"
                  :placeholder="$t('patientForm.riskFactorsPlaceholder')"
                />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.allergies") }}:</span>
                <input
                  v-model="formData.allergies"
                  type="text"
                  class="modern-input"
                  :placeholder="$t('patientForm.allergiesPlaceholder')"
                />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.medications") }}:</span>
                <input
                  v-model="formData.medications"
                  type="text"
                  class="modern-input"
                  :placeholder="$t('patientForm.medicationsPlaceholder')"
                />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.heartProcedures") }}:</span>
                <input
                  v-model="formData.heart_procedures"
                  type="text"
                  class="modern-input"
                  :placeholder="$t('patientForm.heartProceduresPlaceholder')"
                />
              </label>
            </div>
          </div>
        </div>

        <button type="submit" class="modern-submit-btn" :disabled="auth.loading">
          {{ $t("modifyPersonalInfo.save") }}
          <svg class="submit-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M5 12L10 17L20 7"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
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
import { reactive, ref, onMounted, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/authStore";

const { t } = useI18n();
const auth = useAuthStore();

const message = ref("");
const messageType = ref("");

const formData = reactive({
  weight: "",
  height: "",
  age: "",
  bp_systolic: "",
  bp_diastolic: "",
  alcohol_use: "",
  activity: "",
  conditions: "",
  risk_factors: "",
  allergies: "",
  medications: "",
  heart_procedures: "",
});

const splitToArray = (v) => {
  const s = (v ?? "").trim();
  return s ? s.split(",").map((x) => x.trim()).filter(Boolean) : [];
};

const loadFromStore = () => {
  const p = auth.user?.patient_info;
  if (!p) return;

  formData.weight = p.weight ?? "";
  formData.height = p.height ?? "";
  formData.age = p.age ?? "";

  const bp = p.avg_blood_pressure ?? {};
  formData.bp_systolic = bp.systolic ?? "";
  formData.bp_diastolic = bp.diastolic ?? "";

  formData.alcohol_use = p.alcohol_use ?? "";
  formData.activity = p.activity ?? "";

  formData.conditions = (p.conditions ?? []).join(", ");
  formData.risk_factors = (p.risk_factors ?? []).join(", ");
  formData.allergies = (p.allergies ?? []).join(", ");
  formData.medications = (p.medications ?? []).join(", ");
  formData.heart_procedures = (p.heart_procedures ?? []).join(", ");
};

onMounted(async () => {
  await auth.fetchUser();
  loadFromStore();
});

watch(
  () => auth.user,
  () => {
    loadFromStore();
  },
  { deep: true }
);

const handleSubmit = async () => {
  if (!auth.isAuthenticated) return;

  message.value = "";
  messageType.value = "";

  const bp = {
    systolic: formData.bp_systolic === "" ? null : Number(formData.bp_systolic),
    diastolic: formData.bp_diastolic === "" ? null : Number(formData.bp_diastolic),
  };

  const payload = {
    patient_info: {
      weight: formData.weight === "" ? null : Number(formData.weight),
      height: formData.height === "" ? null : Number(formData.height),
      age: formData.age === "" ? undefined : Number(formData.age),
      conditions: splitToArray(formData.conditions),
      avg_blood_pressure: bp,
      risk_factors: splitToArray(formData.risk_factors),
      alcohol_use: formData.alcohol_use || null,
      allergies: splitToArray(formData.allergies),
      activity: formData.activity || null,
      medications: splitToArray(formData.medications),
      heart_procedures: splitToArray(formData.heart_procedures),
    },
  };

  try {
    await auth.updateProfile(payload);
    await auth.fetchUser();
    loadFromStore();

    message.value = t("modifyPersonalInfo.saveSuccess");
    messageType.value = "success";
  } catch (error) {
    console.error("Profile update failed:", error);
    message.value = error?.response?.data?.detail || t("modifyPersonalInfo.saveError");
    messageType.value = "error";
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