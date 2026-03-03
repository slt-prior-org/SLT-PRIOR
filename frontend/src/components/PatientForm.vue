<template>
  <div class="modal-overlay" role="dialog" aria-modal="true" :aria-label="$t('patientForm.title')">
    <div class="modal">
      <!-- Header -->
      <div class="modal-header">
        <div class="modal-title-wrap">
          <h2 class="modal-title">{{ $t("patientForm.title") }}</h2>
        </div>

        <button class="close-btn" type="button" @click="closeForm" aria-label="Close">
          ✖
        </button>
      </div>

      <form class="form" @submit.prevent="submitForm">
        <div class="grid-2">
          <div class="field">
            <label class="label">{{ $t("patientForm.weight") }} <span class="unit">({{ $t("units.kg") }})</span></label>
            <input v-model="patient.weight" type="number" required>
          </div>

          <div class="field">
            <label class="label">{{ $t("patientForm.height") }} <span class="unit">({{ $t("units.cm") }})</span></label>
            <input v-model="patient.height" type="number" required>
          </div>
        </div>

        <div class="field">
          <label class="label">{{ $t("patientForm.conditions") }}</label>
          <input
            v-model="patient.conditions"
            :placeholder="$t('patientForm.conditionsPlaceholder')"
          >
        </div>

        <div class="grid-2">
          <div class="field">
            <label class="label">{{ $t("patientForm.avgBloodPressure") }}</label>
            <input v-model="patient.avg_blood_pressure" placeholder="120/80">
          </div>

          <div class="field">
            <label class="label">{{ $t("patientForm.activity") }}</label>
            <input v-model="patient.activity">
          </div>
        </div>

        <div class="field">
          <label class="label">{{ $t("patientForm.riskFactors") }}</label>
          <input
            v-model="patient.risk_factors"
            :placeholder="$t('patientForm.riskFactorsPlaceholder')"
          >
        </div>

        <div class="field">
          <label class="label">{{ $t("patientForm.allergies") }}</label>
          <input
            v-model="patient.allergies"
            :placeholder="$t('patientForm.allergiesPlaceholder')"
          >
        </div>

        <div class="field">
          <label class="label">{{ $t("patientForm.alcoholUse") }}</label>
          <input v-model="patient.alcohol_use">
        </div>

        <div class="field">
          <label class="label">{{ $t("patientForm.medications") }}</label>
          <input
            v-model="patient.medications"
            :placeholder="$t('patientForm.medicationsPlaceholder')"
          >
        </div>

        <div class="field">
          <label class="label">{{ $t("patientForm.heartProcedures") }}</label>
          <input
            v-model="patient.heart_procedures"
            :placeholder="$t('patientForm.heartProceduresPlaceholder')"
          >
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit">
            {{ $t("patientForm.save") }}
          </button>
          <button class="btn btn-ghost" type="button" @click="closeForm">
            {{ $t("patientForm.skip") }}
          </button>
        </div>
      </form>

      <div v-if="userId" class="user-id-section">
        <div class="success">
          <div class="success-dot" aria-hidden="true"></div>
          <div>
            <p class="success-title">{{ $t("user_saved") }}</p>
            <p class="success-text">
              {{ $t("user_id") }} <strong>{{ userId }}</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { createUser } from "@/api/users";

export default {
  props: ["show"],
  emits: ["close"],
  data() {
    return {
      userId: null,
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
    async submitForm() {
      try {
        const formattedData = {
          user_id: this.userId,
          weight: Number(this.patient.weight),
          height: Number(this.patient.height),
          conditions:
            this.patient.conditions.trim() !== ""
              ? this.patient.conditions
                  .split(",")
                  .map((item) => item.trim())
                  .filter((item) => item !== "")
              : [],
          avg_blood_pressure: this.patient.avg_blood_pressure,
          risk_factors:
            this.patient.risk_factors.trim() !== ""
              ? this.patient.risk_factors
                  .split(",")
                  .map((item) => item.trim())
                  .filter((item) => item !== "")
              : [],
          alcohol_use: this.patient.alcohol_use,
          allergies:
            this.patient.allergies.trim() !== ""
              ? this.patient.allergies
                  .split(",")
                  .map((item) => item.trim())
                  .filter((item) => item !== "")
              : [],
          activity: this.patient.activity,
          medications:
            this.patient.medications.trim() !== ""
              ? this.patient.medications
                  .split(",")
                  .map((item) => item.trim())
                  .filter((item) => item !== "")
              : [],
          heart_procedures:
            this.patient.heart_procedures.trim() !== ""
              ? this.patient.heart_procedures
                  .split(",")
                  .map((item) => item.trim())
                  .filter((item) => item !== "")
              : [],
        };

        const response = await createUser(formattedData);

        if (response) {
          this.userId = response;

          localStorage.setItem("isLoggedIn", "true");
          localStorage.setItem("user", JSON.stringify({ userId: response }));
          window.dispatchEvent(new CustomEvent("authChange"));
        }
      } catch (error) {
        console.error("Virhe tallennuksessa:", error);
      }
    },
    closeForm() {
      this.$emit("close");
    },
  },
};
</script>

<style scoped>
/* Overlay matches the soft modern feel */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px;
  z-index: 1000;
}

/* Modal matches the white card style used on your welcome screen */
.modal {
  position: relative;
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  overflow: auto;

  background: #ffffff;
  border: 1px solid #dbeafe;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);

  padding: 18px 18px 16px;
  font-family: Arial, sans-serif;
  color: #0f172a;
}

/* Header row */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 14px;
}

.modal-title-wrap {
  min-width: 0;
}

.modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.modal-subtitle {
  margin: 6px 0 0;
  font-size: 12.5px;
  line-height: 1.5;
  color: #64748b;
}

.close-btn {
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #64748b;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  cursor: pointer;
  display: grid;
  place-items: center;
}
.close-btn:hover {
  background: #f8fafc;
  color: #0f172a;
}

/* Form layout */
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  font-weight: 800;
  font-size: 12px;
  color: #0f172a;
}

.unit {
  font-weight: 700;
  color: #64748b;
  margin-left: 4px;
}

input {
  width: 100%;
  padding: 12px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  background: #f8fafc;
  box-sizing: border-box;
  font-size: 14px;
  color: #0f172a;
}

input:focus {
  outline: none;
  border-color: #93c5fd;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
  background: #ffffff;
}

/* Buttons match your blue primary */
.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 6px;
}

.btn {
  border: none;
  border-radius: 14px;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.05s ease, background-color 0.2s ease, box-shadow 0.2s ease;
}

.btn:active {
  transform: scale(0.98);
}

.btn-primary {
  background: #1d4ed8;
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(29, 78, 216, 0.25);
}
.btn-primary:hover {
  background: #1e40af;
}

.btn-ghost {
  background: #ffffff;
  color: #0f172a;
  border: 1px solid #e2e8f0;
}
.btn-ghost:hover {
  background: #f8fafc;
}

/* Saved user success block fits modern look */
.user-id-section {
  margin-top: 14px;
}

.success {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid #bbf7d0;
  background: #f0fdf4;
}

.success-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #22c55e;
  margin-top: 4px;
  flex: 0 0 auto;
}

.success-title {
  margin: 0;
  font-weight: 900;
  color: #166534;
  font-size: 13px;
}

.success-text {
  margin: 4px 0 0;
  color: #166534;
  font-size: 12.5px;
}

/* Responsive */
@media (max-width: 640px) {
  .modal {
    max-width: 96vw;
    padding: 16px 14px 14px;
    border-radius: 18px;
  }

  .grid-2 {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>