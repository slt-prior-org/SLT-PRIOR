<template>
  <div :class="['message', fromClass, extraClass]">
    <div class="bubble-wrapper">
      <span class="sender-label">
        {{ formattedSender }}
      </span>

      <div class="bubble" v-html="text" />

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
})

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

  if (props.from === "professional") return t("sender.professional")

  return props.from
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

/* NEEDS REVIEW */
.message.other.needs-review .bubble {
  background: #fff3cd;
  color: #856404;
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
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  border-radius: 9999px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  margin-top: 10px;
}
.sources-toggle:hover {
  background: #f8fafc;
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
  color: #475569;
  line-height: 1.45;
}

@media (max-width: 768px) {
  .bubble-wrapper {
    max-width: 88%;
  }
}


</style>
