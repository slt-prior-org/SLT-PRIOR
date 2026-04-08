<template>
  <div class="modal-overlay">
    <div class="modal">

      <!-- HEADER -->
      <div class="modal-header">
        <div class="patient-info">
          <div class="patient-name">
            {{ $t("professional.patient") }} #{{ chat?.user_id }}
          </div>
        </div>

        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- LAST MESSAGE -->
      <div class="section">

        <div class="section-title">
          {{ $t("professional.lastMessage") }}
        </div>

        <div class="message-box">
          {{ chat?.last_message || "" }}
        </div>

      </div>

      <!-- META CARDS -->
      <div class="meta-grid">

        <div class="meta-card">
          <div class="meta-label">
            {{ $t("professional.status") }}
          </div>
          <div class="meta-value">
            {{ $t("professional.waiting") }}
          </div>
        </div>

        <div class="meta-card">
          <div class="meta-label">
            {{ $t("professional.received") }}
          </div>
          <div class="meta-value">
            {{ formatTime(chat?.updated_at) }}
          </div>
        </div>

      </div>

      <!-- ACTIONS -->
      <div class="modal-actions">
        <AppButton variant="primary" @click="$emit('claim')">
          {{ $t("professional.claim") }}
        </AppButton>

        <AppButton variant="neutral" @click="$emit('close')">
          {{ $t("professional.close") }}
        </AppButton>

      </div>

    </div>
  </div>
</template>

<script setup>
import AppButton from "@/components/ui/AppButton.vue"
import { useI18n } from "vue-i18n"

defineProps({
  chat: Object
})

const { locale } = useI18n()

function formatTime(date) {
  if (!date) return ""

  const lang = locale.value === "fi" ? "fi-FI" : "en-US"

  return new Date(date).toLocaleTimeString(lang, {
    hour: "2-digit",
    minute: "2-digit"
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

/* MODAL */
.modal {
  background: #f8fafc;
  border-radius: 16px;
  width: 640px;
  max-width: 95%;
  padding: 0;
  box-shadow: 0 20px 50px rgba(0,0,0,0.15);
  overflow: hidden;
}

/* HEADER */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  background: #eef2f7;
}

.patient-name {
  font-weight: 600;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #2d445a;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  outline: none;
  border-radius: 8px;
}

.close-btn:hover {
  background: #f0f6ff;
  color: #0f172a;
}

.close-btn:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 1px;
}

/* SECTION */
.section {
  padding: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #94a3b8;
  margin-bottom: 10px;
  text-transform: uppercase;
}

/* MESSAGE */
.message-box {
  background: #e2e8f0;
  border-radius: 14px;
  padding: 14px 16px;
  font-size: 17px;
  line-height: 1.5;

  max-height: 200px;
  overflow-y: auto;
}

/* META GRID */
.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 0 20px 20px;
}

.meta-card {
  background: #eef2f7;
  border-radius: 12px;
  padding: 12px 14px;
}

.meta-label {
  font-size: 15px;
  font-weight: 700;
  color: #1264a3;
  margin-bottom: 4px;
}

.meta-value {
  font-size: 15px;
  font-weight: 600;
}

/* ACTIONS */
.modal-actions {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e5e7eb;
  justify-content: flex-end;
}
</style>