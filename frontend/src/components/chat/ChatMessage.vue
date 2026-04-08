<template>
  <!-- System / info message -->
  <div v-if="isInfo" class="system-wrapper">
    <div class="system-divider">
      <span>{{ t("chat.closed") }}</span>
    </div>
    <div class="system-message">
      {{ $t("chat.closedDescription") }}
    </div>
  </div>

  <!-- Normal chat message -->
  <div v-else :class="['message', fromClass, extraClass]">
    <div class="bubble-wrapper">
      <span class="sender-label">
        {{ formattedSender }}
      </span>

      <div class="bubble">
        <template v-if="requiresConfirmation || guidelineExcerpt">{{ $t('guidelineFound') }}</template>
        <template v-else-if="requiresProfessional">{{ $t('forwardedToProfessional') }}</template>
        <template v-else-if="isForwardConfirmation">{{ $t('confirmForwarded') }}</template>
        <span v-else-if="isEmergency && fromClass === 'other'" v-html="$t('emergencyMessage')" />
        <span v-else v-html="text" />
      </div>
      <div
        v-if="guidelineExcerpt && fromClass === 'other'"
        class="guideline-citation"
        role="note"
      >
        <div class="citation-header">
          <span class="citation-label">{{ $t('guidelineExcerpt') }}</span>
        </div>
        <blockquote class="citation-text">{{ guidelineExcerpt }}</blockquote>
        <div class="citation-source">
          {{ $t('guidelineSource') }}:
          <button v-if="guidelineSourceUrl" class="citation-source-link" @click="openPdf">
            {{ guidelineSource }}
          </button>
          <span v-else>{{ guidelineSource }}</span>
        </div>
      </div>
      <div
        v-if="requiresConfirmation && !confirmationAnswered && fromClass === 'other'"
        class="confirmation-buttons"
      >
        <p class="confirmation-question">{{ $t('confirmationQuestion') }}</p>
        <button class="btn-yes" @click="$emit('confirm-helpful')">
          {{ $t('confirmYes') }}
        </button>
        <button class="btn-no" @click="$emit('confirm-needs-forward')">
          {{ $t('confirmNo') }}
        </button>
      </div>

      <!-- Toggle button -->
      <button
        v-if="fromClass !== 'self' && normalizedSources.length"
        class="sources-toggle"
        @click="showSources = !showSources"
      >
        {{ showSources ? "Hide sources" : "Show sources" }}
      </button>

      <!-- Sources -->
      <div
        v-if="fromClass !== 'self' && normalizedSources.length && showSources"
        class="sources"
      >
        <div class="sources-title">
          Sources
        </div>

        <ul class="sources-list">
          <li
            v-for="source in normalizedSources"
            :key="`${source.source}-${source.index}`"
            class="sources-item"
          >
            <div class="source-name">
              [{{ source.index }}] {{ source.source }}
              <span v-if="source.pages?.length">
                · {{ formatPages(source.pages) }}
              </span>
              <span v-else-if="source.page">
                · p. {{ source.page }}
              </span>
            </div>

            <div v-if="source.preview" class="source-preview">
              {{ source.preview }}
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue"
import { useI18n } from "vue-i18n"
import { api } from "@/services/api"

const { t } = useI18n()
const showSources = ref(false);

// Komponentin ottamat vastaan: kuka lähetti, tekstisisältö ja mahdolliset lisäluokat
const props = defineProps({
  from: {
    type: String,
    required: true,
  },
  text: {
    type: String,
    default: "",
  },
  sources: {
    type: Array,
    default: () => []
  },
  extraClass: {
    type: [String, Array, Object],
    default: "",
  },
  guidelineExcerpt: {
    type: String,
    default: null,
  },
  guidelineSource: {
    type: String,
    default: null,
  },
  guidelineSourceUrl: {
    type: String,
    default: null,
  },
  requiresConfirmation: {
    type: Boolean,
    default: false,
  },
  requiresProfessional: {
    type: Boolean,
    default: false,
  },
  isForwardConfirmation: {
    type: Boolean,
    default: false,
  },
  isEmergency: {
    type: Boolean,
    default: false,
  },
  confirmationAnswered: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['confirm-helpful', 'confirm-needs-forward'])

async function openPdf() {
  if (!props.guidelineSourceUrl) return
  try {
    const response = await api.get(props.guidelineSourceUrl, { responseType: "blob" })
    const url = URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }))
    window.open(url, "_blank", "noopener,noreferrer")
  } catch (e) {
    console.error("Failed to open PDF:", e)
  }
}

const isInfo = computed(() => {
  return props.from === "info"
})

// Lasketaan CSS-luokka lähettäjän perusteella (self = käyttäjä, other = botti/muu)
const fromClass = computed(() => {
  if (props.from === "self" || props.from === "user") return "self"
  if (props.from === "professional") return "professional"
  if (props.from === "info") return "info"
  return "other"
})

// Muotoillaan lähettäjän nimi käännösten perusteella
const formattedSender = computed(() => {
  if (props.from === "self" || props.from === "user") {
    return t("sender.customer")
  }

  if (
    props.from === "other" ||
    props.from === "bot" ||
    props.from === "assistant"
  ) {
    return t("sender.bot")
  }

  if (props.from === "professional") return t("sender.professional")

  return ""
})

const normalizedSources = computed(() => {
// Lähteiden sivunumeroiden muotoilu: yksittäinen sivu "p. X", useampi "pp. X, Y, Z"
  if (!Array.isArray(props.sources)) return []
  return props.sources
    .filter((source) => source && source.source)
    .map((source, index) => ({
      ...source,
      index: source.index ?? index + 1,
      pages: Array.isArray(source.pages) ? source.pages : [],
      preview: typeof source.preview === "string" ? source.preview.trim() : "",
    }))
})

// Lähteiden sivunumeroiden muotoilu: yksittäinen sivu "p. X", useampi "pp. X, Y, Z"
function formatPages(pages) {
  if (!pages?.length) return ""

  if (pages.length === 1) {
    return `p. ${pages[0]}`
  }

  return `pp. ${pages.join(", ")}`
}

</script>

<style scoped>
/* Perusviestin asettelu Flexboxilla */
.message {
  display: flex;
  margin-bottom: 16px;
}

/* Viestien kohdistus: omat viestit oikealle, muiden vasemmalle */
.message.self {
  justify-content: flex-end;
}
.message.other {
  justify-content: flex-start;
}

.bubble-wrapper {
  position: relative;
  display: inline-block;
  max-width: 65%;
}

/* Lähettäjän nimen tyylit ja piilotus omissa viesteissä */
.sender-label {
  display: block;
  font-size: 12px;
  color: #2d445a;
  margin: 0 0 6px;
}
.message.self .sender-label {
  text-align: right;
  padding-right: 8px;
  display: none; /* Piilotetaan oma nimi tilan säästämiseksi */
}

.message.other .sender-label {
  text-align: left;
  padding-left: 8px;
}

/* Viestikuplan perusmuotoilu: pyöristys, välit ja tekstin rivitys */
.bubble {
  position: relative;
  max-width: 100%;
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.5;
  white-space: pre-wrap;
  box-sizing: border-box;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 18px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

/* Botin kuplan värit (harmaa) */
.message.other .bubble {
  background: #f1f5f9;
  color: #0f172a;
}

/* Käyttäjän kuplan värit (vihreä) */
.message.self .bubble {
  background: #16a34a;
  color: #ffffff;
}

/* Kuplan "häntä" (pieni kolmio) vasemmalle puolelle */
.message.other .bubble::after {
  content: "";
  position: absolute;
  left: -6px;
  top: 14px;
  width: 12px;
  height: 12px;
  background: #f1f5f9;
  transform: rotate(45deg);
}

/* Kuplan "häntä" (pieni kolmio) oikealle puolelle */
.message.self .bubble::after {
  content: "";
  position: absolute;
  right: -6px;
  top: 16px;
  width: 14px;
  height: 12px;
  background: #16a34a;
  transform: rotate(45deg);
}

.guideline-citation {
  margin-top: 10px;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-left: 4px solid #16a34a;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 15px;
  max-width: 95%;
}
.citation-header { color: #15803d; font-weight: 600; font-size: 13px; margin-bottom: 8px; }
.citation-text { margin: 0 0 6px; font-style: italic; line-height: 1.6; color: #0f172a; }
.citation-source { color: #2d445a; font-size: 13px; }
.citation-source-link {
  background: none;
  border: none;
  padding: 2px 4px;
  color: #15803d;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
  transition: all 0.2s ease;
  outline: none;
  border-radius: 4px;
}

.citation-source-link:hover {
  color: #166534;
  background: rgba(22, 163, 74, 0.08);
}

.citation-source-link:focus-visible {
  outline: 2px solid #15803d;
  outline-offset: 1px;
}

.confirmation-buttons {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.confirmation-question {
  font-size: 14px;
  color: #374151;
  margin: 0 0 4px;
}
.btn-yes, .btn-no {
  padding: 10px 20px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  outline: none;
}

.btn-yes:focus-visible,
.btn-no:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 1px;
}

.btn-yes {
  background: #16a34a;
  color: white;
}

.btn-yes:hover {
  background: #15803d;
  box-shadow: 0 2px 8px rgba(22, 163, 74, 0.3);
}

.btn-yes:active {
  background: #166534;
}

.btn-no {
  background: #eef2f8;
  color: #1d1d1d;
  border: 1px solid #d0d5e5;
}

.btn-no:hover {
  background: #e3e8f3;
  border-color: #bcc4d5;
}

.btn-no:active {
  background: #d8dce9;
}

/* NEEDS REVIEW */
.message.other.needs-review .bubble {
  background: #fff3cd;
  color: #6b4803;
  border: 1px solid #ffc107;
}

.message.other.needs-review .bubble::after {
  background: #fff3cd;
}

/* EMERGENCY */
.message.other.emergency .bubble {
  background: #f8d7da;
  color: #721c24;
  border: 2px solid #dc3545;
  font-weight: bold;
}

.message.other.emergency .bubble::after {
  background: #f8d7da;
}

/* Lähteiden toggle-painikkeen ja listan tyylit */
.sources-toggle-wrap {
  margin-top: 10px;
}
.sources-toggle {
  border: 1px solid #d0d5e5;
  background: #eef2f8;
  color: #1d1d1d;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 10px;
  transition: all 0.2s ease;
  outline: none;
}

.sources-toggle:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 1px;
}

.sources-toggle:hover {
  background: #e3e8f3;
  border-color: #bcc4d5;
}

.sources-toggle:active {
  background: #d8dce9;
}

/* Lähdelistan tyyli: tausta, reunus ja sisennys */
.sources {
  margin-top: 10px;
  padding: 10px 14px;
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
}
.sources-title {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  margin-bottom: 8px;
}
.sources-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.sources-item + .sources-item {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e2e8f0;
}
.source-name {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}
.source-preview {
  margin-top: 4px;
  font-size: 12px;
  color: #1d2e3e;
  line-height: 1.45;
}

@media (max-width: 768px) {
  .bubble-wrapper {
    max-width: 88%;
  }
}



/* Professional message */
.message.professional {
  justify-content: flex-start;
}

.message.professional .bubble {
  background: #e8f5e9;
  color: #1b5e20;
}

.message.professional .bubble::after {
  content: "";
  position: absolute;
  left: -6px;
  top: 18px;
  width: 12px;
  height: 12px;
  background: #e8f5e9;
  transform: rotate(45deg);
}

.message.professional .sender-label {
  text-align: left;
  padding-left: 8px;
}

/* System wrapper */
.system-wrapper {
  margin: 28px 0;
}

/* Divider line */
.system-divider {
  display: flex;
  align-items: center;
  text-align: center;
  font-size: 13px;
  color: #2d445a;
  margin-bottom: 10px;
}

.system-divider::before,
.system-divider::after {
  content: "";
  flex: 1;
  border-bottom: 1px solid #cbd5f5;
}

.system-divider span {
  padding: 0 12px;
  font-weight: 500;
  white-space: nowrap;
}

/* System message text */
.system-message {
  text-align: center;
  font-size: 16px;
  color: #1d2e3e;
  line-height: 1.5;
  max-width: 70%;
  margin: 0 auto;
}
</style>
