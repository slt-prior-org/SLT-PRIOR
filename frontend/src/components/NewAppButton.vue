<template>
  <button
    :class="[
      'app-btn',
      `variant-${variant}`,
      `size-${size}`
    ]"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: "primary" // primary | neutral | danger
  },
  size: {
    type: String,
    default: "md" // sm | md | lg
  },
  disabled: Boolean
})

defineEmits(["click"])
</script>

<style scoped>
.app-btn{
  border:none;
  border-radius:10px;
  cursor:pointer;
  white-space:nowrap;
  transition:0.15s ease;
  font-weight:500;
}

/* VARIANTS */

.variant-primary{
  background:#1264a3;
  color:white;
}

.variant-primary:hover{
  background:#0f5791;
}

.variant-neutral{
  background:#eef2f8;
  color:#2b2f36;
}

.variant-neutral:hover{
  background:#e3e8f3;
}

.variant-danger{
  background:#d9534f;
  color:white;
}

.variant-danger:hover{
  background:#c74440;
}

/* SIZES */

.size-sm{
  padding:6px 12px;
  font-size:12px;
  border-radius:8px;
}

.size-md{
  padding:10px 18px;
  font-size:14px;
}

.size-lg{
  padding:12px 24px;
  font-size:15px;
}

/* DISABLED */

.app-btn:disabled{
  opacity:0.6;
  cursor:not-allowed;
}
</style>