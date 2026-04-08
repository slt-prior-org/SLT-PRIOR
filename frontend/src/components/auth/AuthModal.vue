<template>
  <div v-if="show" class="modal-overlay" @click.self="close">
    <div class="modal">
      <button class="close-btn" @click="close">✕</button>

      <div class="auth-header">
        <h2 class="auth-title">{{ $t("auth.title") }}</h2>

        <p class="auth-subtitle">{{ $t("auth.subtitle") }}</p>
      </div>

      <div class="auth-tabs">
        <button
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >
          {{ $t("login.title") }}
        </button>

        <button
          :class="{ active: activeTab === 'register' }"
          @click="activeTab = 'register'"
        >
          {{ $t("register.title") }}
        </button>
      </div>

      <div class="auth-content">
        <UserLogin
          v-if="activeTab === 'login'"
          @close="close"
          @login-success="$emit('login-success')"
        />

        <UserRegister
          v-if="activeTab === 'register'"
          @close="close"
          @register-success="$emit('register-success')"
        />
      </div>
    </div>
  </div>
</template>

<script>
import UserLogin from "@/components/auth/UserLogin.vue"
import UserRegister from "@/components/auth/UserRegister.vue"

export default {
  components: {
    UserLogin,
    UserRegister,
  },

  props: {
    show: Boolean,
    initialTab: {
      type: String,
      default: 'login',
    },
  },

  emits: ["close", "login-success", "register-success"],

  data() {
    return {
      activeTab: this.initialTab || 'login',
    }
  },

  watch: {
    initialTab(newTab) {
      this.activeTab = newTab || 'login';
    },
    show(val) {
      if (val) {
        this.activeTab = this.initialTab || 'login';
      }
    }
  },

  methods: {
    close() {
      this.$emit("close")
    },
  },
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal {
  width: 420px;
  max-width: 92%;
  background: white;
  border-radius: 20px;
  padding: 28px 28px 30px;
  box-shadow:
    0 20px 60px rgba(15, 23, 42, 0.15),
    0 8px 24px rgba(15, 23, 42, 0.08);
  position: relative;
  font-family:
    ui-sans-serif,
    system-ui,
    -apple-system,
    "Segoe UI",
    Roboto,
    Arial,
    "Noto Sans",
    "Liberation Sans",
    sans-serif;

  animation: modalEnter 0.18s ease;
}

@keyframes modalEnter {
  from {
    transform: translateY(8px) scale(0.98);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

.close-btn {
  position: absolute;
  right: 14px;
  top: 14px;
  border: none;
  background: #eef2f8;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: #1d1d1d;
  outline: none;
}

.close-btn:hover {
  background: #e3e8f3;
}

.close-btn:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 1px;
}

.auth-header {
  text-align: center;
  margin-bottom: 18px;
}

.auth-title {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
}

.auth-subtitle {
  font-size: 14px;
  color: #2d445a;
  margin: 0;
}

.auth-tabs {
  display: flex;
  gap: 6px;
  background: #f1f5f9;
  padding: 6px;
  border-radius: 12px;
  margin-bottom: 20px;
}

.auth-tabs button {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1d3548;
  cursor: pointer;
  transition: all 0.15s ease;
}

.auth-tabs button:hover {
  background: #e2e8f0;
}

.auth-tabs button.active {
  background: white;
  color: #1d4ed8;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.auth-content {
  margin-top: 4px;
}
</style>
