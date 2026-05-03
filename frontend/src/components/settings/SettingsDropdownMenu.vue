<template>
  <div class="menu">
    <template v-for="(item, index) in items" :key="item.key">
      <AppButton :class="['menu-item', item.key === 'logout' ? 'logout' : '']" variant="neutral" @click="handleClick(item)">
        <span class="menu-icon">
          <template v-if="item.key === 'edit-health-profile'">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="currentColor"
              viewBox="0 0 24 24"
              width="18"
              height="18"
            >
              <path
                d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 
                       4.42 3 7.5 3c1.74 0 3.41 0.81 4.5 2.09C13.09 3.81 
                       14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 
                       6.86-8.55 11.54L12 21.35z"
              />
            </svg>
          </template>

          <template v-else-if="item.key === 'logout'">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="2"
              stroke="currentColor"
              width="18"
              height="18"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1"
              />
            </svg>
          </template>
        </span>
        <span>{{ $t(item.labelKey) }}</span>
      </AppButton>

      <div v-if="index < items.length - 1" class="menu-divider"></div>
    </template>
  </div>

  <div class="menu-backdrop" @click="$emit('close')" />
</template>

<script setup>
import AppButton from "@/components/ui/AppButton.vue"

defineProps({
  items: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(["close"])

function handleClick(item) {
  item.action?.()
  emit("close")
}
</script>

<style scoped>
.menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 220px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.12);
  z-index: 1001;
  padding: 2px 2px;
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  border: none;
  background: transparent;
  font-size: 16px;
  text-align: left;
  width: 100%;
  padding: 12px 16px;
  border-radius: 6px;
  cursor: pointer;
  color: #0f172a;
  transition: background 0.2s;
}

.menu-item:hover {
  background: #f1f5f9;
}
.menu-item.logout {
  color: #d32d2f !important;
  font-weight: 600;
}
.menu-item.logout .menu-icon svg {
  color: #d32d2f !important;
  stroke: #d32d2f !important;
}
.menu-item.logout:hover {
  background: #ffeaea;
  color: #b71c1c !important;
}
.menu-item.logout:hover .menu-icon svg {
  color: #b71c1c !important;
  stroke: #b71c1c !important;
}

.menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 22px;
  height: 22px;
}

.menu-icon svg {
  width: 100%;
  height: 100%;
}

.menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
}
</style>
