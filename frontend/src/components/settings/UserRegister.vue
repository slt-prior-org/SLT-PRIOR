<template>
  <div class="settings-section">
    <div v-if="step === 1">
      <h2>{{ $t("register.title") }}</h2>

      <div class="name-fields">
        <input
          type="text"
          v-model="register.firstName"
          :placeholder="$t('register.firstName')"
          required
        >
        <input
          type="text"
          v-model="register.lastName"
          :placeholder="$t('register.lastName')"
          required
        >
      </div>

      <input
        type="text"
        v-model="register.email"
        :placeholder="$t('register.email')"
        required
      >

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
        <input v-model="patient.weight" type="number" required>

        <label>{{ $t("patientForm.height") }} (cm):</label>
        <input v-model="patient.height" type="number" required>

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
        <input v-model="patient.alcohol_use">

        <label>{{ $t("patientForm.allergies") }}:</label>
        <input
          v-model="patient.allergies"
          :placeholder="$t('patientForm.allergiesPlaceholder')"
        >

        <label>{{ $t("patientForm.activity") }}:</label>
        <input v-model="patient.activity">

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
import { createUser } from '@/api/users';

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
        firstName: "",
        lastName: "",
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

      const firstName = this.register.firstName?.trim();
      const lastName = this.register.lastName?.trim();
      const email = this.register.email?.trim();
      const password = this.register.password;

      if (!firstName || !lastName || !email || !password) {
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
          firstName: this.register.firstName.trim(),
          lastName: this.register.lastName.trim(),
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

        const response = await createUser(formattedData);

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
.name-fields {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  margin-top: 12px;
}
.name-fields input { flex: 1; }

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