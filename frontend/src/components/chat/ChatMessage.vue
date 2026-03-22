<template>
  <div :class="['message', fromClass, extraClass]">
    <div class="bubble-wrapper">
      <span class="sender-label">
        {{ formattedSender }}
      </span>
      <div class="bubble" v-html="text" />
      <div
        v-if="guidelineExcerpt && fromClass === 'other'"
        class="guideline-citation"
        role="note"
      >
        <div class="citation-header">
          <span class="citation-label">{{ $t('guidelineExcerpt') }}</span>
        </div>
        <blockquote class="citation-text">{{ guidelineExcerpt }}</blockquote>
        <div class="citation-source">{{ $t('guidelineSource') }}: {{ guidelineSource }}</div>
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
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { useI18n } from "vue-i18n"

const { t } = useI18n()

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
  requiresConfirmation: {
    type: Boolean,
    default: false,
  },
  confirmationAnswered: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['confirm-helpful', 'confirm-needs-forward'])

// Lasketaan CSS-luokka lähettäjän perusteella (self = käyttäjä, other = botti/muu)
const fromClass = computed(() => {
  if (props.from === "self" || props.from === "user") return "self"
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

  return props.from
})
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
  max-width: 95%;
}

/* Lähettäjän nimen tyylit ja piilotus omissa viesteissä */
.sender-label {
  display: block;
  font-size: 12px;
  color: #64748b;
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
  padding: 16px 20px;
  border-radius: 22px;
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
  top: 18px;
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
  top: 22px;
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
.citation-source { color: #64748b; font-size: 13px; }

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
  padding: 8px 20px;
  border-radius: 20px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}
.btn-yes {
  background: #16a34a;
  color: white;
}
.btn-no {
  background: #f1f5f9;
  color: #374151;
  border: 1px solid #cbd5e1;
}
</style>
