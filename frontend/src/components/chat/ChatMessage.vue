<template>
  <div :class="['message', fromClass, extraClass]">
    <div class="bubble-wrapper">
      <span class="sender-label">
        {{ formattedSender }}
      </span>
      <div class="bubble" v-html="text" />
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
    required: true
  },
  text: {
    type: String,
    default: ""
  },
  extraClass: {
    type: [String, Array, Object],
    default: ""
  }
})

// Lasketaan CSS-luokka lähettäjän perusteella (self = käyttäjä, other = botti/muu)
const fromClass = computed(() => (props.from === "self" ? "self" : "other"))

// Muotoillaan lähettäjän nimi käännösten perusteella
const formattedSender = computed(() => {
  if (props.from === "self") return t("sender.customer")
  if (props.from === "other") return t("sender.bot")
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
.message.self { justify-content: flex-end; }
.message.other { justify-content: flex-start; }

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
</style>