<template>
  <div>
    <!-- STEP 1 : REGISTER FORM -->
    <form v-if="step === 1" class="auth-section" @submit.prevent="goToStep2">
      <div class="form-group">
        <input
          v-model="register.email"
          type="email"
          :placeholder="$t('register.email')"
          required
          autocomplete="email"
        />
      </div>

      <div class="form-group">
        <input
          v-model="register.password"
          type="password"
          :placeholder="$t('register.password')"
          required
          autocomplete="new-password"
        />
      </div>

      <AppButton
        type="submit"
        variant="primary"
        class="auth-button"
        :disabled="loading"
      >
        {{ $t("register.continue") }}
      </AppButton>

      <p v-if="error" class="auth-error">
        {{ error }}
      </p>
    </form>

    <!-- STEP 2 : HEALTH PROFILE MODAL -->
    <PatientProfileModal
      v-if="step === 2"
      v-model:patient="patient"
      :loading="loading"
      @submit="submitAll"
      @back="step = 1"
      @close="closeForm"
    />
  </div>
</template>

<script>
import { useAuthStore } from "@/stores/authStore"
import AppButton from "@/components/ui/AppButton.vue"
import PatientProfileModal from "./PatientProfileModal.vue"

export default {
  components: { AppButton, PatientProfileModal },
  props: ["show"],
  emits: ["close", "register-success"],
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
        alcohol_use: "",
        allergies: "",
        activity: "",
        medications: "",
        heart_procedures: "",
      },
    }
  },
  created() {
    this.auth = useAuthStore()
  },
  methods: {
    goToStep2() {
      const email = this.register.email?.trim()
      const password = this.register.password

      if (!email || !password) {
        this.error = "Please fill all required fields."
        return
      }

      this.error = null
      // Move on to patient form
      this.step = 2
    },

    splitToArray(value) {
      const s = (value ?? "").trim()
      return s
        ? s
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean)
        : []
    },

    async submitAll() {
      this.error = null
      this.loading = true

      try {
        // Build ONE final payload that includes BOTH pages
        // patient info (page 2)
        const patientInfo = {
          weight:
            this.patient.weight === ""
              ? undefined
              : Number(this.patient.weight),
          height:
            this.patient.height === ""
              ? undefined
              : Number(this.patient.height),
          age: this.patient.age === "" ? undefined : Number(this.patient.age),
          conditions: this.splitToArray(this.patient.conditions),
          risk_factors: this.splitToArray(this.patient.risk_factors),
          alcohol_use:
            this.patient.alcohol_use === ""
              ? undefined
              : this.patient.alcohol_use,
          allergies: this.splitToArray(this.patient.allergies),
          activity:
            this.patient.activity === "" ? undefined : this.patient.activity,
          medications: this.splitToArray(this.patient.medications),
          heart_procedures: this.splitToArray(this.patient.heart_procedures),
        }

        if (
          this.patient.avg_bp_systolic !== "" &&
          this.patient.avg_bp_diastolic !== ""
        ) {
          patientInfo.avg_blood_pressure = {
            systolic: Number(this.patient.avg_bp_systolic),
            diastolic: Number(this.patient.avg_bp_diastolic),
          }
        }

        const formattedData = {
          // registration (page 1)
          email: this.register.email.trim(),
          password: this.register.password,
          role: "patient",
          patient_info: patientInfo,
        }
        await this.auth.register(formattedData) // stores token + user
        this.$emit("register-success")
        this.$emit("close")
      } catch (err) {
        this.error =
          err?.response?.data?.detail || err?.message || "Register failed."
        this.step = 1
      } finally {
        this.loading = false
      }
    },

    closeForm() {
      this.step = 1
      this.$emit("close")
    },
  },
}
</script>

<style scoped>
.auth-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group {
  display: flex;
}

.form-group input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #dbe3ef;
  font-size: 14px;
  outline: none;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.form-group input:focus {
  border-color: #3a5bdc;
  box-shadow: 0 0 0 3px rgba(58, 91, 220, 0.15);
}

.auth-button {
  margin-top: 8px;
  width: 100%;
  padding: 12px 20px !important;
  font-size: 15px !important;
  border-radius: 10px !important;
}

.auth-error {
  margin-top: 6px;
  font-size: 13px;
  color: #b91c1c;
  background: #fee2e2;
  padding: 8px 10px;
  border-radius: 8px;
}
</style>
