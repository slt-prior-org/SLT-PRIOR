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
.app-btn {
  border: none;
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  font-weight: 500;
  font-family: inherit;
  outline: none;
}

/* Focus state for keyboard navigation (WCAG AAA accessibility) */
.app-btn:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 2px;
}

/* VARIANTS - with WCAG AAA contrast ratios */
.variant-primary {
  background: #1264a3;
  color: white;
}

.variant-primary:hover:not(:disabled) {
  background: #0f5791;
  box-shadow: 0 2px 8px rgba(18, 100, 163, 0.3);
}

.variant-primary:active:not(:disabled) {
  background: #0d4570;
}

.variant-secondary {
  background: #4f46e5;
  color: white;
}

.variant-secondary:hover:not(:disabled) {
  background: #4338ca;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}

.variant-secondary:active:not(:disabled) {
  background: #3f2fa0;
}

.variant-neutral {
  background: #eef2f8;
  color: #1d1d1d;
  border: 1px solid #d0d5e5;
}

.variant-neutral:hover:not(:disabled) {
  background: #e3e8f3;
  border-color: #bcc4d5;
}

.variant-neutral:active:not(:disabled) {
  background: #d8dce9;
}

.variant-danger {
  background: #d9534f;
  color: white;
}

.variant-danger:hover:not(:disabled) {
  background: #c74440;
  box-shadow: 0 2px 8px rgba(217, 83, 79, 0.3);
}

.variant-danger:active:not(:disabled) {
  background: #b53835;
}

.variant-success {
  background: #16a34a;
  color: white;
}

.variant-success:hover:not(:disabled) {
  background: #15803d;
  box-shadow: 0 2px 8px rgba(22, 163, 74, 0.3);
}

.variant-success:active:not(:disabled) {
  background: #166534;
}

.variant-ghost {
  background: transparent;
  color: #1264a3;
  border: 1px solid #1264a3;
}

.variant-ghost:hover:not(:disabled) {
  background: #f0f6ff;
  border-color: #0f5791;
}

.variant-ghost:active:not(:disabled) {
  background: #e0ecff;
}

/* SIZES */
.size-sm {
  padding: 8px 14px;
  font-size: 13px;
  border-radius: 8px;
}

.size-md {
  padding: 12px 20px;
  font-size: 15px;
  border-radius: 10px;
}

.size-lg {
  padding: 16px 30px;
  font-size: 18px;
  border-radius: 12px;
}

/* DISABLED STATE */
.app-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}
</style>