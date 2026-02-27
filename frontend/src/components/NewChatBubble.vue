<template>
  <div :class="['message', sender]">
    <div class="bubble-wrapper">

      <span class="sender-label">
        {{ formattedSender }}
      </span>

      <div class="bubble">
        <slot>{{ content }}</slot>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
  sender: {
    type: String,
    required: true
  },
  content: {
    type: String,
    default: ""
  }
})

const formattedSender = computed(() => {
  if (props.sender === "user") return "Asiakas"
  if (props.sender === "bot") return "Bot"
  if (props.sender === "professional") return "Ammattilainen"
  return props.sender
})
</script>

<style scoped>
.message{
  display:flex;
  margin-bottom:16px;
}

.message.user{ justify-content:flex-end; }

.message.bot,
.message.professional{ justify-content:flex-start; }

.bubble{
  max-width:85%;
  padding:16px 20px;
  border-radius:22px;
  border-style:solid;
  border-color:#e0eff8;
  border-width:1px;
  font-size:16px;
  line-height:1.5;
}

.message.user .bubble{
  background:#ffffff;
  color:black;
}

.message.bot .bubble{
  background:#f0f7fc;
}

.message.professional .bubble{
  background:#f0f7fc;
}

.bubble-wrapper{
  position:relative;
  display:inline-block;
}

.sender-label{
  font-size:12px;
  color:#7a869a;
  margin-left:6px;
}

.message.user .sender-label{
  text-align:right;
  margin-right:6px;
}
</style>