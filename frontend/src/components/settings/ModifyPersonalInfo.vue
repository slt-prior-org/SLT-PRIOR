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
          <!-- Basic Info -->
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

          <!-- Health Info -->
          <div class="form-card">
            <h3 class="form-card-title">{{ $t("modifyPersonalInfo.healthInfo") }}</h3>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.avgBloodPressure") }}:</span>
                <input
                  v-model="formData.avg_blood_pressure_text"
                  type="text"
                  class="modern-input"
                  placeholder="120/80"
                />
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.alcoholUse") }}:</span>
                <select v-model="formData.alcohol_use" class="modern-input">
                  <option value="">{{ $t("options.none") }}</option>
                  <option value="occasional">{{ $t("options.occasional") }}</option>
                  <option value="moderate">{{ $t("options.moderate") }}</option>
                  <option value="heavy">{{ $t("options.heavy") }}</option>
                </select>
              </label>
            </div>

            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.activity") }}:</span>
                <select v-model="formData.activity" class="modern-input">
                  <option value="">{{ $t("options.none") }}</option>
                  <option value="sedentary">{{ $t("options.sedentary") }}</option>
                  <option value="light">{{ $t("options.light") }}</option>
                  <option value="active">{{ $t("options.active") }}</option>
                  <option value="very_active">{{ $t("options.very_active") }}</option>
                </select>
              </label>
            </div>
          </div>

          <!-- Medical Info -->
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

        <button type="submit" class="modern-submit-btn">
          {{ $t("modifyPersonalInfo.save") }}
          <svg class="submit-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 12L10 17L20 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
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
import { reactive, ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/authStore";

const { t } = useI18n();
const auth = useAuthStore();

const message = ref("");
const messageType = ref("");

const formData = reactive({
  weight: "",
  height: "",
  avg_blood_pressure_text: "",
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

const parseBpText = (text) => {
  const s = (text ?? "").trim();
  if (!s) return { systolic: null, diastolic: null };
  const parts = s.split("/").map((x) => x.trim());
  const sys = Number(parts[0]);
  const dia = Number(parts[1]);
  return {
    systolic: Number.isFinite(sys) ? sys : null,
    diastolic: Number.isFinite(dia) ? dia : null,
  };
};

const loadFromStore = () => {
  const p = auth.user?.patient_info;
  if (!p) return;

  formData.value.weight = p.weight ?? "";
  formData.value.height = p.height ?? "";

  const bp = p.avg_blood_pressure;
  formData.value.avg_blood_pressure_text =
    bp?.systolic != null && bp?.diastolic != null ? `${bp.systolic}/${bp.diastolic}` : "";

  formData.value.alcohol_use = p.alcohol_use ?? "";
  formData.value.activity = p.activity ?? "";

  formData.value.conditions = (p.conditions ?? []).join(", ");
  formData.value.risk_factors = (p.risk_factors ?? []).join(", ");
  formData.value.allergies = (p.allergies ?? []).join(", ");
  formData.value.medications = (p.medications ?? []).join(", ");
  formData.value.heart_procedures = (p.heart_procedures ?? []).join(", ");
};

onMounted(async () => {
  await auth.fetchUser();
  loadFromStore();
});

const handleSubmit = async () => {
  if (!auth.isAuthenticated) return;

  message.value = "";
  messageType.value = "";

  const bp = parseBpText(formData.value.avg_blood_pressure_text);

  const payload = {
    patient_info: {
      weight: formData.value.weight === "" ? null : Number(formData.value.weight),
      height: formData.value.height === "" ? null : Number(formData.value.height),

      avg_blood_pressure: bp,
      alcohol_use: formData.value.alcohol_use || null,
      activity: formData.value.activity || null,

      conditions: splitToArray(formData.value.conditions),
      risk_factors: splitToArray(formData.value.risk_factors),
      allergies: splitToArray(formData.value.allergies),
      medications: splitToArray(formData.value.medications),
      heart_procedures: splitToArray(formData.value.heart_procedures),
    },
  };

  try {
    await auth.updateProfile(payload);
    message.value = t("modifyPersonalInfo.saveSuccess");
    messageType.value = "success";

    // Refresh form with saved values
    await auth.fetchUser();
    loadFromStore();
  } catch (error) {
    console.error(error);
    message.value = t("modifyPersonalInfo.saveError");
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