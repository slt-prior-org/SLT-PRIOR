<template>
  <div class="settings-section">
    <div v-if="step === 1">
      <h2>{{ $t("register.title") }}</h2>
      <div class="email-field">
        <input
          type="text"
          v-model="register.email"
          :placeholder="$t('register.email')"
          required
        >
      </div>

      <div class="password-field">
        <input
          type="password"
          v-model="register.password"
          :placeholder="$t('register.password')"
          required
        >
      </div>

      <AppButton variant="primary" :disabled="loading" @click="goToStep2">
        {{ $t("register.continue")}}
      </AppButton>

      <p v-if="error" class="login-message">{{ error }}</p>
    </div>

    <div v-else-if="step === 2">
      <h2>{{ $t("patientForm.title") }}</h2>
      <h5>{{ $t("register.optional") }}</h5>

      <form @submit.prevent="submitAll">
        <label>{{ $t("patientForm.weight") }} (kg):</label>
        <input v-model="patient.weight" type="number">

        <label>{{ $t("patientForm.height") }} (cm):</label>
        <input v-model="patient.height" type="number">

        <label>{{ $t("patientForm.age") }}:</label>
        <input v-model.number="patient.age" type="number">

        <label>{{ $t("patientForm.conditions") }}:</label>
        <input
          v-model="patient.conditions"
          :placeholder="$t('patientForm.conditionsPlaceholder')"
        >

        <label>{{ $t("patientForm.avgBloodPressure") }}:</label>
        <div class="bp-row">
          <input v-model="patient.avg_bp_systolic" type="number" placeholder="Systolic" >
          <input v-model="patient.avg_bp_diastolic" type="number" placeholder="Diastolic">
        </div>

        <label>{{ $t("patientForm.riskFactors") }}:</label>
        <input
          v-model="patient.risk_factors"
          :placeholder="$t('patientForm.riskFactorsPlaceholder')"
        >

        <label>{{ $t("patientForm.alcoholUse") }}:</label>
        <select v-model="patient.alcohol_use">
          <option disabled value="">
            {{ $t("patientForm.alcoholUse") }}
          </option>
          <option value="none">
            {{ $t("patientForm.alcoholNone") }}
          </option>
          <option value="rare">
            {{ $t("patientForm.alcoholRare") }}
          </option>
          <option value="monthly">
            {{ $t("patientForm.alcoholMonthly") }}
          </option>
          <option value="weekly">
            {{ $t("patientForm.alcoholWeekly") }}
          </option>
          <option value="daily">
            {{ $t("patientForm.alcoholDaily") }}
          </option>
        </select>

        <label>{{ $t("patientForm.allergies") }}:</label>
        <input
          v-model="patient.allergies"
          :placeholder="$t('patientForm.allergiesPlaceholder')"
        >

        <label>{{ $t("patientForm.activity") }}:</label>
        <select v-model="patient.activity">
          <option disabled value="none">
            {{ $t("patientForm.activityNone") }}
          </option>
          <option value="sedentary">
            {{ $t("patientForm.activityNone") }}
          </option>
          <option value="light">
            {{ $t("patientForm.activityLight") }}
          </option>
          <option value="moderate">
            {{ $t("patientForm.activityModerate") }}
          </option>
          <option value="vigorous">
            {{ $t("patientForm.activityActive") }}
          </option>
        </select>

        <label>{{ $t("patientForm.medications") }}:</label>
        <input
          v-model="patient.medications"
          :placeholder="$t('patientForm.medicationsPlaceholder')"
        >

        <label>{{ $t("patientForm.heartProcedures") }}:</label>
        <input
          v-model="patient.heart_procedures"
          :placeholder="$t('patientForm.heartProceduresPlaceholder')"
        >

        <div class="form-actions">

          <AppButton type="button" variant="neutral" size="sm" @click="step = 1">
            {{ $t("back")}}
          </AppButton>

          <AppButton type="submit" variant="primary" size="sm">
            {{ $t("register.register") }}
          </AppButton>
        </div>
      </form>

      <p v-if="error" class="login-message">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from "@/stores/authStore";
import AppButton from "@/components/ui/AppButton.vue";

export default {
  components: { AppButton },
  props: ["show"],
  emits: ["close"],
  data() {
    return {
      step: 1,
      loading: false,
      error: null,

      userId: null,

      // Page 1 data
      register: {
        email: "",
        password: "",
        role: ""
      },

      // Page 2 data
      patient: {
        weight: "",
        height: "",
        age: "",
        conditions: "",
        avg_bp_systolic: "",
        avg_bp_diastolic: "",
        risk_factors: "",
        alcohol_use: "none",
        allergies: "",
        activity: "sedentary",
        medications: "",
        heart_procedures: "",
      },
    };
  },
  created() {
    this.auth = useAuthStore();
  },
  methods: {
    goToStep2() {
      this.error = null;

      const email = this.register.email?.trim();
      const password = this.register.password;

      if (!email || !password) {
        this.error = "Please fill all required fields.";
        return;
      }

      // Move on to patient form
      this.step = 2;
    },

    splitToArray(value) {
      const s = (value ?? "").trim();
      return s
        ? s.split(",").map(x => x.trim()).filter(Boolean)
        : [];
    },

    async submitAll() {
      this.error = null;
      this.loading = true;

      try {
        // Build ONE final payload that includes BOTH pages
        // patient info (page 2)
        const patientInfo = {
          weight: this.patient.weight === "" ? undefined : Number(this.patient.weight),
          height: this.patient.height === "" ? undefined : Number(this.patient.height),
          age: this.patient.age === "" ? undefined : Number(this.patient.age),
          conditions: this.splitToArray(this.patient.conditions),
          risk_factors: this.splitToArray(this.patient.risk_factors),
          alcohol_use: this.patient.alcohol_use,
          allergies: this.splitToArray(this.patient.allergies),
          activity: this.patient.activity,
          medications: this.splitToArray(this.patient.medications),
          heart_procedures: this.splitToArray(this.patient.heart_procedures)
        };

        if (
          this.patient.avg_bp_systolic !== "" &&
          this.patient.avg_bp_diastolic !== ""
        ) {
          patientInfo.avg_blood_pressure = {
            systolic: Number(this.patient.avg_bp_systolic),
            diastolic: Number(this.patient.avg_bp_diastolic),
          };
        }

        const formattedData = {
          // registration (page 1)
          email: this.register.email.trim(),
          password: this.register.password,
          role : "patient",
          patient_info: patientInfo
        };
        await this.auth.register(formattedData); // stores token + user
        this.$emit("close");
      } catch (err) {
        this.error = err?.response?.data?.detail || err?.message || "Register failed.";
      } finally {
        this.loading = false;
      }
    },

    closeForm() {
      this.$emit("close");
    },
  },
};
</script>

<style scoped>
/* keep your existing styles or import */
.email-field {
  display: flex;
  margin-bottom: 12px;
  margin-top: 12px;
}

.password-field {
  margin-top: 12px;
  margin-bottom: 12px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.login-message {
  margin-top: 1rem;
  font-size: 0.9rem;
  padding: 10px;
  border-radius: 4px;
}

.user-id-section { margin-top: 20px; }

@import "@/assets/settingsstyles.css";
</style>