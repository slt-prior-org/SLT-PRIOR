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

      <button :disabled="loading" @click="goToStep2">
        {{ $t("register.continue")}}
      </button>

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

        <label>{{ $t("patientForm.conditions") }}:</label>
        <input
          v-model="patient.conditions"
          :placeholder="$t('patientForm.conditionsPlaceholder')"
        >

        <label>{{ $t("patientForm.avgBloodPressure") }}:</label>
        <input v-model="patient.avg_blood_pressure">

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
          <option disabled value="">
            {{ $t("patientForm.activity") }}
          </option>
          <option value="none">
            {{ $t("patientForm.activityNone") }}
          </option>
          <option value="light">
            {{ $t("patientForm.activityLight") }}
          </option>
          <option value="moderate">
            {{ $t("patientForm.activityModerate") }}
          </option>
          <option value="active">
            {{ $t("patientForm.activityActive") }}
          </option>
          <option value="very_active">
            {{ $t("patientForm.activityVeryActive") }}
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

          <button type="button" @click="step = 1">
            {{ $t("back")}}
          </button>

          <button type="submit">
            {{ $t("register.register") }}
          </button>
        </div>
      </form>

      <p v-if="error" class="login-message">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { registerUser } from '@/api/users';

export default {
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
        conditions: "",
        avg_blood_pressure: "",
        risk_factors: "",
        alcohol_use: "",
        allergies: "",
        activity: "",
        medications: "",
        heart_procedures: "",
      },
    };
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
        const formattedData = {
          // registration (page 1)
          email: this.register.email.trim(),
          password: this.register.password,
          role : "patient",

          // patient info (page 2)
          patient_info: {
            weight: Number(this.patient.weight),
            height: Number(this.patient.height),
            conditions: this.splitToArray(this.patient.conditions),
            avg_blood_pressure: this.patient.avg_blood_pressure,
            risk_factors: this.splitToArray(this.patient.risk_factors),
            alcohol_use: this.patient.alcohol_use,
            allergies: this.splitToArray(this.patient.allergies),
            activity: this.patient.activity,
            medications: this.splitToArray(this.patient.medications),
            heart_procedures: this.splitToArray(this.patient.heart_procedures)
          }
        };

        const response = await registerUser(formattedData);
        console.log("Response from MongoDB:", response);

        this.userId = response;

        localStorage.setItem("isLoggedIn", "true");
        localStorage.setItem("user", JSON.stringify({ userId: this.userId }));
        window.dispatchEvent(new CustomEvent("authChange"));
        this.closeForm();

      } catch (err) {
        console.error(err);
        this.error = err?.message ?? "Submit failed.";
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