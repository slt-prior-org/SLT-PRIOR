<script setup>
import { ref } from "vue"
//import { useRouter } from "vue-router"
//import { logoutUser } from "@/services/authService"
import { Settings } from "lucide-vue-next"
import SettingsDrawer from "./NewSettingsDrawer.vue"

defineProps({
  queueCount: Number,
  closedCount: Number,
  user: Object
})

//const router = useRouter()

// TODO: implementoidaan myöhemmin
async function handleLogout() {
  console.log("Logout clicked (not implemented yet)")
  //router.push("/login")
}

/* drawer visibility */
const showSettings = ref(false)
</script>

<template>
  <div class="header">

    <!-- LEFT -->
    <div class="left">
      <div class="logo-placeholder"></div>
      <span class="app-name">HeartWise</span>
    </div>

    <!-- CENTER -->
    <div class="center">
      <span class="badge">{{ queueCount }} JONO</span>
      <span class="badge light">{{ closedCount }} VALMIS</span>
    </div>

    <!-- RIGHT -->
    <div class="right">
      <div class="user">
        <strong>{{ user?.name || "..." }}</strong>
        <small>{{ user?.role || "" }}</small>
      </div>

      <!-- SETTINGS BUTTON -->
      <button class="gear" @click="showSettings = true">
        <Settings size="18" />
      </button>
    </div>

  </div>

  <!-- SETTINGS DRAWER -->
  <SettingsDrawer
    v-if="showSettings"
    :user="user"
    @close="showSettings = false"
    @logout="handleLogout"
  />
</template>

<style scoped>
.header {
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:16px 28px;
  background:white;
  border-bottom:1px solid #eee;
}

.left { display:flex; gap:12px; align-items:center; }

.logo-placeholder {
  width:40px;
  height:40px;
  border-radius:8px;
  background:#dfe7ff;
}

.center { display:flex; gap:12px; }

.badge {
  background:#e8eefc;
  color:#3a5bdc;
  padding:6px 14px;
  border-radius:20px;
  font-size:13px;
}

.badge.light {
  background:#eef1f6;
  color:#5f6c7b;
}

.right { display:flex; gap:16px; align-items:center; }

.user { display:flex; flex-direction:column; font-size:13px; }

/* SETTINGS BUTTON */
.gear {
  background:#eef2f8;
  border:none;
  border-radius:12px;
  padding:8px 10px;
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
}
</style>