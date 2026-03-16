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
            </div>

          <div class="form-card">
            <h3 class="form-card-title">{{ $t("modifyPersonalInfo.healthInfo") }}</h3>
            <div class="form-group">
              <label class="input-label">
                <span>{{ $t("personalInfo.avgBloodPressure") }}:</span>
                <input v-model="formData.avg_blood_pressure_text" type="text" class="modern-input" placeholder="120/80" />
              </label>
            </div>
            </div>

          <div class="form-card">
            <h3 class="form-card-title">{{ $t("modifyPersonalInfo.medicalInfo") }}</h3>
            </div>
        </div>

        <AppButton type="submit" variant="primary" class="modern-submit-btn">
          {{ $t("modifyPersonalInfo.save") }}
        </AppButton>

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
import AppButton from "@/components/ui/AppButton.vue";

const { t } = useI18n();
const auth = useAuthStore(); // Käytetään keskitettyä käyttäjänhallintaa (Pinia/Vuex)

const message = ref("");
const messageType = ref("");

// Lomakkeen reaktiivinen tila
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

// Apuohjelma: muuttaa pilkulla erotellun tekstin siistiksi taulukoksi
const splitToArray = (v) => {
  const s = (v ?? "").trim();
  return s ? s.split(",").map((x) => x.trim()).filter(Boolean) : [];
};

// Apuohjelma: purkaa "120/80" tekstin ylä- ja alapaineeksi numeroina
const parseBpText = (text) => {
  const s = (text ?? "").trim();
  if (!s) return { systolic: null, diastolic: null };
  const parts = s.split("/").map((x) => x.trim());
  return {
    systolic: Number(parts[0]) || null,
    diastolic: Number(parts[1]) || null,
  };
};

// Alustetaan lomake storesta löytyvillä tiedoilla
const loadFromStore = () => {
  const p = auth.user?.patient_info;
  if (!p) return;

  formData.weight = p.weight ?? "";
  formData.height = p.height ?? "";
  
  // Yhdistetään verenpaine takaisin näytettäväksi tekstiksi
  const bp = p.avg_blood_pressure;
  formData.avg_blood_pressure_text = 
    bp?.systolic != null ? `${bp.systolic}/${bp.diastolic}` : "";

  // Muutetaan taulukot takaisin pilkulla erotelluksi tekstiksi käyttäjälle
  formData.conditions = (p.conditions ?? []).join(", ");
  // ... muut kentät samalla tavalla
};

// Haetaan käyttäjän tiedot heti, kun komponentti ladataan
onMounted(async () => {
  await auth.fetchUser();
  loadFromStore();
});

// Lomakkeen lähetys
const handleSubmit = async () => {
  if (!auth.isAuthenticated) return;

  message.value = "";
  
  // Muunnetaan lomakkeen tiedot takaisin API:n ymmärtämään muotoon
  const bp = parseBpText(formData.avg_blood_pressure_text);
  const payload = {
    patient_info: {
      weight: formData.weight === "" ? null : Number(formData.weight),
      height: formData.height === "" ? null : Number(formData.height),
      avg_blood_pressure: bp,
      alcohol_use: formData.alcohol_use || null,
      activity: formData.activity || null,
      // Käytetään apufunktiota tekstin pilkkomiseen taulukoksi
      conditions: splitToArray(formData.conditions),
      risk_factors: splitToArray(formData.risk_factors),
      allergies: splitToArray(formData.allergies),
      medications: splitToArray(formData.medications),
      heart_procedures: splitToArray(formData.heart_procedures),
    },
  };

  try {
    // Lähetetään päivitys palvelimelle
    await auth.updateProfile(payload);
    message.value = t("modifyPersonalInfo.saveSuccess");
    messageType.value = "success";
    
    // Päivitetään paikallinen tila vastaamaan tallennettuja tietoja
    await auth.fetchUser();
    loadFromStore();
  } catch (error) {
    message.value = t("modifyPersonalInfo.saveError");
    messageType.value = "error";
  }
};
</script>

<style scoped>
/* Tuodaan ulkoinen tyylitiedosto ja määritetään muutama paikallinen tyyli */
@import "@/assets/settingsstyles.css";

.login-prompt {
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  padding: 20px;
  text-align: center;
}
</style>