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

const props = defineProps({
  // "self" | "other"
  from: {
    type: String,
    required: true
  },
  text: {
    type: String,
    default: ""
  },

  // can be string/array/object just like Vue :class
  extraClass: {
    type: [String, Array, Object],
    default: ""
  }
})

const fromClass = computed(() => (props.from === "self" ? "self" : "other"))

const formattedSender = computed(() => {
  if (props.from === "self") return t("sender.customer")
  if (props.from === "other") return t("sender.bot")
  return props.from
})
</script>

<style scoped>
.message{
  display:flex;
  margin-bottom:16px;
}

/* alignment */
.message.self{ justify-content:flex-end; }
.message.other{ justify-content:flex-start; }

.bubble-wrapper{
  position:relative;
  display:inline-block;
  max-width: 95%;
}

/* sender label aligned to side */
.sender-label{
  display:block;
  font-size:12px;
  color:#64748b;
  margin: 0 0 6px;
}
.message.self .sender-label{ 
    text-align:right; 
    padding-right:8px; 
    display: none;
}

.message.other .sender-label{ 
    text-align:left; 
    padding-left:8px; 
}

/* bubble base */
.bubble{
  position: relative;
  max-width: 100%;
  padding:16px 20px;
  border-radius:22px;
  font-size:16px;
  line-height:1.5;
  white-space: pre-wrap;
  box-sizing: border-box;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif;
  font-size: 18px; 

  /* allow breaking long strings with no spaces */
  overflow-wrap: anywhere;
  word-break: break-word;
  min-width: 0;

  /* allow tail to render */
  overflow: visible;
}

/* BOT bubble (left) */
.message.other .bubble{
  background:#f1f5f9;
  color:#0f172a;
}

/* USER bubble (right) */
.message.self .bubble{
  background:#16a34a;
  color:#ffffff;
}

.message.other .bubble::after{
  content:"";
  position:absolute;
  left:-6px;
  top:18px;
  width:12px;
  height:12px;
  background:#f1f5f9;                 
  transform: rotate(45deg);
}

.message.self .bubble::after{
  content:"";
  position:absolute;
  right:-6px;
  top:22px;
  width:14px;
  height:12px;
  background:#16a34a;
  transform: rotate(45deg);
}
</style>