<template>
  <div class="patient-form">
    <div class="form-header">
      <h2 class="title">
        {{ $t("patientForm.healthProfile") }}
      </h2>

      <p class="subtitle">
        {{
          mode === "edit"
            ? $t("patientForm.updateHealthInfo")
            : $t("patientForm.finishRegistration")
        }}
      </p>

      <div class="info-box">
        {{ $t("patientForm.description") }}
        <strong>{{ $t("patientForm.optional") }}</strong>
      </div>
    </div>

    <!-- HEALTH METRICS -->

    <div class="health-grid">
      <div class="metric-field">
        <label>{{ $t("patientForm.weight") }}</label>
        <div class="metric-input">
          <input type="number" v-model="localPatient.weight" />
          <span class="unit">kg</span>
        </div>
      </div>

      <div class="metric-field">
        <label>{{ $t("patientForm.height") }}</label>
        <div class="metric-input">
          <input type="number" v-model="localPatient.height" />
          <span class="unit">cm</span>
        </div>
      </div>

      <div class="metric-field">
        <label>{{ $t("patientForm.age") }}</label>
        <div class="metric-input">
          <input type="number" v-model="localPatient.age" />
          <span class="unit">{{ $t("patientForm.years") }}</span>
        </div>
      </div>

      <div class="metric-field">
        <label>{{ $t("patientForm.avgBloodPressure") }}</label>

        <div class="metric-input bp-input">
          <input
            type="number"
            v-model="localPatient.avg_bp_systolic"
            placeholder="120"
          />

          <span class="separator">/</span>

          <input
            type="number"
            v-model="localPatient.avg_bp_diastolic"
            placeholder="80"
          />

          <span class="unit">mmHg</span>
        </div>
      </div>
    </div>

    <!-- FORM FIELDS -->

    <div class="form-fields">
      <div class="form-group">
        <label>{{ $t("patientForm.conditions") }}</label>
        <input
          v-model="localPatient.conditions"
          :placeholder="$t('patientForm.conditionsPlaceholder')"
        />
      </div>

      <div class="form-group">
        <label>{{ $t("patientForm.riskFactors") }}</label>
        <input
          v-model="localPatient.risk_factors"
          :placeholder="$t('patientForm.riskFactorsPlaceholder')"
        />
      </div>

      <div class="form-group">
        <label>{{ $t("patientForm.alcoholUse") }}</label>
        <select v-model="localPatient.alcohol_use">
          <option disabled value="">
            {{ $t("patientForm.alcoholUsePlaceholder") }}
          </option>
          <option value="none">{{ $t("patientForm.alcoholNone") }}</option>
          <option value="rare">{{ $t("patientForm.alcoholRare") }}</option>
          <option value="monthly">
            {{ $t("patientForm.alcoholMonthly") }}
          </option>
          <option value="weekly">{{ $t("patientForm.alcoholWeekly") }}</option>
          <option value="daily">{{ $t("patientForm.alcoholDaily") }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>{{ $t("patientForm.allergies") }}</label>
        <input
          v-model="localPatient.allergies"
          :placeholder="$t('patientForm.allergiesPlaceholder')"
        />
      </div>

      <div class="form-group">
        <label>{{ $t("patientForm.activity") }}</label>
        <select v-model="localPatient.activity">
          <option disabled value="">
            {{ $t("patientForm.activityPlaceholder") }}
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
      </div>

      <div class="form-group">
        <label>{{ $t("patientForm.medications") }}</label>
        <input
          v-model="localPatient.medications"
          :placeholder="$t('patientForm.medicationsPlaceholder')"
        />
      </div>

      <div class="form-group">
        <label>{{ $t("patientForm.heartProcedures") }}</label>
        <input
          v-model="localPatient.heart_procedures"
          :placeholder="$t('patientForm.heartProceduresPlaceholder')"
        />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    patient: {
      type: Object,
      default: () => ({
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
      }),
    },
    mode: {
      type: String,
      default: "register",
    },
  },

  emits: ["update:patient"],

  computed: {
    localPatient: {
      get() {
        return this.patient
      },
      set(val) {
        this.$emit("update:patient", val)
      },
    },
  },
}
</script>

<style scoped>
.patient-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

/* HEADER */

.title {
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  font-size: 15px;
  color: #6b7280;
  margin-top: 2px;
}

/* INFO BOX */

.info-box {
  margin-top: 10px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e3a8a;

  padding: 12px 14px;
  border-radius: 10px;
  font-size: 14px;
}

.info-box strong {
  font-weight: 600;
}

/* HEALTH GRID */

.health-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

/* FIELD */

.metric-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-field label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

/* INPUT */

.metric-input {
  display: flex;
  align-items: center;
  border: 1px solid #dbe3ef;
  border-radius: 10px;
  padding: 8px 12px;
}

.metric-input input {
  border: none;
  outline: none;
  width: 100%;
  font-size: 15px;
}

.unit {
  font-size: 13px;
  color: #6b7280;
}

/* BLOOD PRESSURE */

.bp-input {
  gap: 6px;
}

.separator {
  color: #6b7280;
}

/* FORM FIELDS */

.form-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #dbe3ef;
}
</style>
