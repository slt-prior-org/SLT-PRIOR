<template>
  <div class="modal-overlay">
    <div class="patient-modal">
      <button class="close-btn" @click="close">✕</button>

      <div class="scrollable-content">
        <PatientForm
          mode="edit"
          :patient="patientData"
          @update:patient="patientData = $event"
        />
      </div>

      <div class="modal-actions">
        <AppButton variant="neutral" @click="close">
          {{ $t("healthProfile.close") }}
        </AppButton>
        <AppButton
          variant="primary"
          :disabled="loading || !isDirty"
          @click="saveProfile"
        >
          {{ $t("healthProfile.save") }}
        </AppButton>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue"
import PatientForm from "@/components/ui/PatientForm.vue"
import AppButton from "@/components/ui/AppButton.vue"
import { useAuthStore } from "@/stores/authStore"

const emit = defineEmits(["close", "profile-update-success"])

const auth = useAuthStore()

// kopio käyttäjän tiedoista (ettei store muutu suoraan)
const patientData = ref({
  ...auth.user.patient_info,

  conditions: fromList(auth.user.patient_info?.conditions),
  risk_factors: fromList(auth.user.patient_info?.risk_factors),
  allergies: fromList(auth.user.patient_info?.allergies),
  medications: fromList(auth.user.patient_info?.medications),
  heart_procedures: fromList(auth.user.patient_info?.heart_procedures),

  avg_bp_systolic: auth.user.patient_info?.avg_blood_pressure?.systolic || "",
  avg_bp_diastolic: auth.user.patient_info?.avg_blood_pressure?.diastolic || "",
})

const originalPatient = ref(
  JSON.stringify({
    ...auth.user.patient_info,
    conditions: fromList(auth.user.patient_info?.conditions),
    risk_factors: fromList(auth.user.patient_info?.risk_factors),
    allergies: fromList(auth.user.patient_info?.allergies),
    medications: fromList(auth.user.patient_info?.medications),
    heart_procedures: fromList(auth.user.patient_info?.heart_procedures),
    avg_bp_systolic: auth.user.patient_info?.avg_blood_pressure?.systolic || "",
    avg_bp_diastolic:
      auth.user.patient_info?.avg_blood_pressure?.diastolic || "",
  }),
)

const isDirty = computed(() => {
  return JSON.stringify(patientData.value) !== originalPatient.value
})

const loading = ref(false)

function close() {
  emit("close")
}

function toList(value) {
  if (!value) return []
  if (Array.isArray(value)) return value

  return value
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean)
}

function fromList(value) {
  if (!value) return ""
  if (Array.isArray(value)) return value.join(", ")
  return value
}

function parseNumber(value) {
  const n = Number(value)
  return !value || isNaN(n) ? null : n
}

async function saveProfile() {
  loading.value = true

  try {
    const payload = {
      ...patientData.value,

      conditions: toList(patientData.value.conditions),
      risk_factors: toList(patientData.value.risk_factors),
      allergies: toList(patientData.value.allergies),
      medications: toList(patientData.value.medications),
      heart_procedures: toList(patientData.value.heart_procedures),

      weight: parseNumber(patientData.value.weight),
      height: parseNumber(patientData.value.height),
      age: parseNumber(patientData.value.age),
    }

    const systolic = parseNumber(patientData.value.avg_bp_systolic)
    const diastolic = parseNumber(patientData.value.avg_bp_diastolic)
    payload.avg_blood_pressure =
      systolic !== null && diastolic !== null ? { systolic, diastolic } : null

    delete payload.avg_bp_systolic
    delete payload.avg_bp_diastolic

    await auth.updateProfile({ patient_info: payload })
    emit("profile-update-success")
    close()
  } catch (err) {
    console.error("Profile update failed", err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.patient-modal {
  width: 760px;
  max-width: 92vw;
  max-height: 90vh;
  background: white;
  border-radius: 14px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  padding: 28px 34px 0 34px;
  position: relative;
  display: flex;
  flex-direction: column;
}

.scrollable-content :deep(.form-header) {
  position: sticky;
  top: 0;
  background: white;
  z-index: 10;
  padding-bottom: 20px;
}

.scrollable-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.close-btn {
  position: absolute;
  right: 6px;
  top: 6px;
  border: none;
  background: #eef2f8;
  width: 28px;
  height: 28px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: #1d1d1d;
  outline: none;
}

.close-btn:hover {
  background: #e3e8f3;
}

.close-btn:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 1px;
}

/* ACTION BUTTONS */

.modal-actions {
  display: flex;
  gap: 10px;
  padding: 20px 34px 28px 34px;
  background: white;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}

.modal-actions button {
  flex: 1;
}
</style>
