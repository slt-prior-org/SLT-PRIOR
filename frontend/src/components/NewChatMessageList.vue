<template>
  <div ref="container" class="message-history">
    <ChatBubble
      v-for="(message, index) in messages"
      :key="message.content + index"
      :sender="message.sender"
      :content="message.content"
    />
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue"
import ChatBubble from "@/components/NewChatBubble.vue"

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  }
})

const container = ref(null)

// auto scroll uusille viesteille
watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (!container.value) return
    container.value.scrollTop = container.value.scrollHeight
  }
)
</script>

<style scoped>
.message-history{
  flex:1;
  overflow-y:auto;
  padding:28px;
  display:flex;
  flex-direction:column;
}
</style>