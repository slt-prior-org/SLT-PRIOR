<template>
  <div class="chat-input-bar">

    <textarea
      v-model="localValue"
      :placeholder="placeholder"
      :disabled="disabled"
      @keydown.enter.exact.prevent="emitSend"
    />

    <div class="actions">
      <AppButton
        v-if="showEdit"
        variant="neutral"
        @click="$emit('toggle-edit')"
        >
        {{ isEditing ? "Valmis" : "Muokkaa viestiä" }}
        </AppButton>

        <AppButton
        variant="primary"
        @click="emitSend"
        >
        Lähetä
        </AppButton>
    </div>

  </div>
</template>

<script setup>
import { ref, watch } from "vue"
import AppButton from "@/components/NewAppButton.vue"

const props = defineProps({
  modelValue: String,
  placeholder: {
    type: String,
    default: "Kirjoita viesti..."
  },
  disabled: Boolean,
  showEdit: Boolean,
  isEditing: Boolean
})

const emit = defineEmits(["update:modelValue", "send", "toggle-edit"])

const localValue = ref(props.modelValue || "")

watch(localValue, v => emit("update:modelValue", v))
watch(() => props.modelValue, v => (localValue.value = v))

function emitSend() {
  if (!localValue.value?.trim()) return
  emit("send", localValue.value)
}
</script>

<style scoped>
.chat-input-bar{
  padding:10px 28px 28px 28px;
  display:flex;
  flex-direction:column;
  gap:12px;
}

.chat-input-bar textarea{
  width:100%;
  border-radius:16px;
  border:1px solid #e0e4ea;
  padding:14px;
  resize:none;
  font-size:15px;
  min-height:110px;
  background:#f0f7fc;
}

.actions{
  display:flex;
  gap:12px;
}
</style>