<template>
  <div class="settings-section">
    <h2>{{ $t("personalInfo.title") }}</h2>

    <div v-if="!auth.isAuthenticated" class="login-prompt">
      <p>{{ $t("personalInfo.loginPrompt") }}</p>
    </div>

    <template v-else>
      <div class="info-section">
        <h3>{{ $t("personalInfo.basicInfo") }}</h3>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.weight") }}: </span>
          <span class="value">
            {{ displayOrNotProvided(patient.weight) }}
            <template v-if="patient.weight != null"> {{ $t("units.kg") }} </template>
          </span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.height") }}: </span>
          <span class="value">
            {{ displayOrNotProvided(patient.height) }}
            <template v-if="patient.height != null"> {{ $t("units.cm") }} </template>
          </span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.age") }}: </span>
          <span class="value">
            {{ displayOrNotProvided(patient.age) }}
          </span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.avgBloodPressure") }}: </span>
          <span class="value">{{ avgBpText }}</span>
        </div>
      </div>

      <div class="info-section">
        <h3>{{ $t("personalInfo.healthInfo") }}</h3>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.alcoholUse") }}: </span>
          <span class="value">{{ patient.alcohol_use ?? $t("personalInfo.notProvided") }}</span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.activity") }}: </span>
          <span class="value">{{ patient.activity ?? $t("personalInfo.notProvided") }}</span>
        </div>
      </div>

      <div class="info-section">
        <h3>{{ $t("personalInfo.medicalInfo") }}</h3>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.conditions") }}: </span>
          <ul v-if="patient.conditions?.length" class="value-list">
            <li v-for="condition in patient.conditions" :key="condition">
              {{ condition }}
            </li>
          </ul>
          <span v-else class="value">{{ $t("personalInfo.notProvided") }}</span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.riskFactors") }}: </span>
          <ul v-if="patient.risk_factors?.length" class="value-list">
            <li v-for="factor in patient.risk_factors" :key="factor">
              {{ factor }}
            </li>
          </ul>
          <span v-else class="value">{{ $t("personalInfo.notProvided") }}</span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.allergies") }}: </span>
          <ul v-if="patient.allergies?.length" class="value-list">
            <li v-for="allergy in patient.allergies" :key="allergy">
              {{ allergy }}
            </li>
          </ul>
          <span v-else class="value">{{ $t("personalInfo.notProvided") }}</span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.medications") }}: </span>
          <ul v-if="patient.medications?.length" class="value-list">
            <li v-for="medication in patient.medications" :key="medication">
              {{ medication }}
            </li>
          </ul>
          <span v-else class="value">{{ $t("personalInfo.notProvided") }}</span>
        </div>

        <div class="info-row">
          <span class="label">{{ $t("personalInfo.heartProcedures") }}: </span>
          <ul v-if="patient.heart_procedures?.length" class="value-list">
            <li v-for="procedure in patient.heart_procedures" :key="procedure">
              {{ procedure }}
            </li>
          </ul>
          <span v-else class="value">{{ $t("personalInfo.notProvided") }}</span>
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

const displayOrNotProvided = (value) => {
  return value && value !== 0 ? value : "—";
};

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

</script>

<style scoped>
@import "@/assets/settingsstyles.css";
</style>