<template>
  <div class="patient-wrapper">

    <!-- BASIC INFO -->
    <div class="card">
      <h3>{{ $t('professional.patientInfo') }}</h3>

      <div class="stats-row">

        <div class="stat-card">
          <span class="label">{{ $t('professional.age') }}</span>
          <b>{{ patient.age ?? '-' }}</b>
        </div>

        <div class="stat-card">
          <span class="label">{{ $t('professional.height') }}</span>
          <b>{{ patient.height != null ? patient.height + ' cm' : '-' }}</b>
        </div>

        <div class="stat-card">
          <span class="label">{{ $t('professional.weight') }}</span>
          <b>{{ patient.weight ?? '-' }} kg</b>
        </div>
      </div>

      <div class="block">
        <span class="label">{{ $t('professional.conditions') }}</span>

        <ul v-if="patient.conditions?.length" class="list">
          <li v-for="(c, i) in patient.conditions" :key="i">
            {{ c }}
          </li>
        </ul>

        <p v-else>-</p>
      </div>

      <div class="block">
        <span class="label">{{ $t('professional.medication') }}</span>

        <ul v-if="patient.medications?.length" class="list">
          <li v-for="(m, i) in patient.medications" :key="i">
            {{ m }}
          </li>
        </ul>

        <p v-else>-</p>
      </div>
    </div>

    <!-- SUMMARY -->
    <div class="card">
      <span class="label">{{ $t('professional.summary') }}</span>

      <div class="summary" v-html="formattedSummary"></div>
    </div>

  </div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
  patient: Object,
  summary: String
})

const formattedSummary = computed(() => {
  if (!props.summary) return ""

  return props.summary
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>")
})
</script>

<style scoped>

.patient-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;

  height: 100%;
  overflow-y: auto;
}

/* CARD */
.card {
  background: white;
  border-radius: 18px;
  padding: 16px 18px;
  border: 1px solid #e5e7eb;

  box-shadow: 0 6px 20px rgba(0,0,0,0.04);
}

.card h3 {
  font-size: clamp(14px, 1vw, 20px);
  color: #606870;
  margin-bottom: 15px;
  text-transform: uppercase;
}

.block {
  margin-bottom: 10px;
}

.label {
  font-size: clamp(13px, 0.7vw, 20px);
  font-weight: 600;
  text-transform: uppercase;
  color: #606870;
  display: block;
  margin-bottom: 7px;
}

.block p {
  margin: 2px 0 0;
  font-size: clamp(12px, 0.7vw, 18px);
}

/* SUMMARY */
.summary {
  font-size: clamp(12px, 0.7vw, 20px);
  line-height: 1.5;
  color: #1e293b;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}

.stat-card {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 10px 12px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  border: 1px solid #e2e8f0;
}

.stat-card .label {
  font-size: clamp(12px, 0.8vw, 20px);
  color: #64748b;
  margin-bottom: 2px;
}

.stat-card b {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.list {
  list-style: none;
  padding-left: 0;
  margin: 4px 0 0;
}

.list li {
  position: relative;
  padding-left: 14px;  /* tila pallukalle */
  margin-bottom: 4px;
  font-size: clamp(12px, 0.7vw, 18px);
  color: #334155;
}

.list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 8px;

  width: 6px;
  height: 6px;

  background: #94a3b8;
  border-radius: 50%;
}

</style>