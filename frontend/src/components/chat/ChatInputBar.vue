<template>
  <div class="chat-input-bar">
    <div class="input-row">
      <textarea
        v-model="localValue"
        :placeholder="placeholder"
        :disabled="inputDisabled"
        @keydown.enter.exact.prevent="trySend"
      />

      <AppButton
        class="send-btn"
        variant="primary"
        :disabled="sendDisabled || !localValue?.trim()"
        @click="trySend"
      >
        {{ t("send") }}
      </AppButton>
    </div>

    <div class="actions" v-if="showEdit">
      <AppButton variant="neutral" @click="$emit('toggle-edit')">
        {{ isEditing ? t("done") : t("editMessage") }}
      </AppButton>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from "vue"
import { useI18n } from "vue-i18n"
import AppButton from "../ui/AppButton.vue"

const { t } = useI18n()

// Komponentin vastaanottamat tiedot (propsit)
const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "" },
  inputDisabled: { type: Boolean, default: false },
  sendDisabled: { type: Boolean, default: false },
  showEdit: Boolean,
  isEditing: Boolean
})

// Tapahtumat, joita komponentti lähettää ylöspäin
const emit = defineEmits(["update:modelValue", "send", "toggle-edit"])

// Paikallinen tila tekstille, jotta v-model toimii sujuvasti
const localValue = ref(props.modelValue || "")

// Synkronoidaan paikallinen muutos ja propseista tuleva data keskenään
watch(localValue, (v) => emit("update:modelValue", v))
watch(() => props.modelValue, (v) => (localValue.value = v || ""))

// Funktio, joka tarkistaa viestin kelvollisuuden ennen lähetystä
function trySend() {
  if (props.sendDisabled) return
  if (!localValue.value?.trim()) return
  emit("send", localValue.value)
}
</script>

<style scoped>
/* Asettelu: pystysuuntainen pino ja elementtien väli */
.chat-input-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Tekstikentän ja napin rivitys */
.input-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

/* Tekstikentän tyylit: joustava leveys ja moderni pyöristys */
.chat-input-bar textarea {
  font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
  flex: 1 1 auto;
  width: 100%;
  border-radius: 16px;
  border: 1px solid #e0e4ea;
  padding: clamp(10px, 1vw, 14px);
  resize: none;
  font-size: clamp(14px, 1vw, 18px);
  min-height: 44px;
  background: #f0f7fc;
  box-sizing: border-box;
}

/* Lähetysnapin kokoasetukset */
.send-btn {
  flex: 0 0 auto;
  height: 50px;
  white-space: nowrap;
}

/* Toimintopainikkeiden sijoittelu oikeaan reunaan */
.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>