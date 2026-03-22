<template>
  <button
    :class="['app-btn', `variant-${variant}`, `size-${size}`]"
    :disabled="disabled"
    :type="type"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  variant: { type: String, default: "primary" }, // primary | neutral | danger
  size: { type: String, default: "md" }, // sm | md | lg
  type: { type: String, default: "button" },
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
.variant-primary{ background:#1264a3; color:white; }
.variant-primary:hover{ background:#0f5791; }

.variant-neutral{ background:#eef2f8; color:#2b2f36; }
.variant-neutral:hover{ background:#e3e8f3; }

.variant-danger{ background:#d9534f; color:white; }
.variant-danger:hover{ background:#c74440; }

/* SIZES */
.size-sm{ padding:10px 16px; font-size:14px; border-radius:8px; }
.size-md{ padding:14px 24px; font-size:18px; }
.size-lg{ padding:16px 30px; font-size:22px; }

/* DISABLED */
.app-btn:disabled{ opacity:0.6; cursor:not-allowed; }
</style>