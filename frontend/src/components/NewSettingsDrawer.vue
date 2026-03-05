<script setup>
import { defineEmits, defineProps } from "vue"
import AppButton from "@/components/NewAppButton.vue"

const emit = defineEmits(["close", "logout"])

defineProps({
  user: Object
})

function close() {
  emit("close")
}

function logout() {
  emit("logout")
}

</script>

<template>
  <div class="overlay" @click.self="close">
    <div class="drawer">

      <!-- HEADER -->
      <div class="drawer-header">
        <h3>Asetukset</h3>
        <AppButton
          variant="neutral"
          size="sm"
          @click="close"
        >
          ✕
        </AppButton>
      </div>

      <!-- USER CARD -->
      <div class="user-card">
        <div class="avatar"></div>

        <div class="user-info">
          <strong>{{ user?.name || "..." }}</strong>
          <span>{{ user?.role || "" }}</span>
        </div>
      </div>

      <!-- ACTIONS -->
      <div class="actions">
        <AppButton variant="danger" @click="logout">
          Kirjaudu ulos
        </AppButton>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* overlay */
.overlay{
  position:fixed;
  inset:0;
  background:rgba(0,0,0,0.25);
  display:flex;
  justify-content:flex-end;
  z-index:999;
}

/* drawer */
.drawer{
  width:320px;
  background:white;
  height:100%;
  padding:24px;
  display:flex;
  flex-direction:column;
  gap:24px;
  box-shadow:-10px 0 30px rgba(0,0,0,0.08);
}

/* header */
.drawer-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
}

/* user card */
.user-card{
  display:flex;
  gap:14px;
  align-items:center;
  padding:16px;
  background:#f8fafc;
  border-radius:18px;
}

.avatar{
  width:48px;
  height:48px;
  border-radius:12px;
  background:#dfe7ff;
}

.user-info{
  display:flex;
  flex-direction:column;
  font-size:14px;
}

/* actions */
.actions{
  margin-top:auto;
  display: flex;
  justify-content:center;
}
</style>