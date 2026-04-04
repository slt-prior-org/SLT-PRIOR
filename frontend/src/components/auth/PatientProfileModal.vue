<template>
  <div class="modal-overlay">
    <div class="patient-modal">
      <button class="close-btn" @click="$emit('close')">✕</button>

      <PatientForm
        :patient="patient"
        @update:patient="$emit('update:patient', $event)"
      />

      <div class="modal-actions">
        <div class="primary-actions">
          <AppButton
            variant="primary"
            :disabled="loading"
            @click="$emit('submit')"
          >
            {{ $t("patientForm.save") }}
          </AppButton>

          <AppButton variant="neutral" @click="$emit('submit')">
            {{ $t("patientForm.skip") }}
          </AppButton>
        </div>

        <AppButton variant="ghost" class="back-button" @click="$emit('back')">
          {{ $t("patientForm.back") }}
        </AppButton>
      </div>
    </div>
  </div>
</template>

<script>
import PatientForm from "../ui/PatientForm.vue"
import AppButton from "@/components/ui/AppButton.vue"

export default {
  components: { PatientForm, AppButton },

  props: {
    patient: Object,
    loading: Boolean,
  },

  emits: ["close", "submit", "back", "update:patient", "register-success"],
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

/* leveämpi modal */

.patient-modal {
  width: 760px;
  max-width: 92vw;

  background: white;
  border-radius: 14px;

  padding: 28px 34px;

  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.close-btn {
  position: absolute;
  top: 14px;
  right: 16px;
  border: none;
  background: none;
  font-size: 20px;
  cursor: pointer;
}

.modal-actions {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.primary-actions {
  display: flex;
  gap: 10px;
}

.primary-actions button {
  flex: 1;
}

.back-button {
  width: 100%;
}
</style>
