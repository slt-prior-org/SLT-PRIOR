<template>
  <form class="auth-section" novalidate @submit.prevent="handleLogin">
    <div class="form-group">
      <input
        type="email"
        v-model="email"
        :placeholder="$t('login.email')"
        required
        autocomplete="email"
      />
    </div>

    <div class="form-group">
      <input
        type="password"
        v-model="password"
        :placeholder="$t('login.password')"
        required
        autocomplete="current-password"
      />
    </div>

    <AppButton
      type="submit"
      class="login-button"
      variant="primary"
      :disabled="loading"
    >
      {{ $t("login.title") }}
    </AppButton>

    <p v-if="error" class="auth-error">
      {{ error }}
    </p>
  </form>
</template>

<script setup>
import { ref } from "vue"
import { useI18n } from "vue-i18n"
import { useAuthStore } from "@/stores/authStore"
import AppButton from "@/components/ui/AppButton.vue"
import { useRouter } from "vue-router"

const emit = defineEmits(["close", "login-success"])

const { t } = useI18n()
const auth = useAuthStore()
const router = useRouter()

const email = ref("")
const password = ref("")
const loading = ref(false)
const error = ref("")

const handleLogin = async () => {
  try {
    loading.value = true
    error.value = ""

    await auth.login(email.value, password.value)

    emit("login-success") // näyttää ilmoituksen
    emit("close") // sulkee modaalin

    if (auth.user?.role === "professional") {
      router.push("/professional")
    } else {
      router.push("/")
    }
  } catch (err) {
    const detail = err?.response?.data?.detail

    const code =
      typeof detail === "object" && detail?.code
        ? detail.code
        : typeof detail === "string"
          ? detail
          : "loginStatus.failed"

    error.value = t(code) === code ? t("loginStatus.invalid_credentials") : t(code)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group {
  display: flex;
}

.form-group input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #dbe3ef;
  font-size: 14px;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
  outline: none;
}

.form-group input:focus {
  border-color: #3a5bdc;
  box-shadow: 0 0 0 3px rgba(58, 91, 220, 0.15);
}

.login-button {
  margin-top: 8px;
  width: 100%;
  padding: 12px 20px !important;
  font-size: 15px !important;
  border-radius: 10px !important;
}

.auth-error {
  margin-top: 6px;
  font-size: 13px;
  color: #b91c1c;
  background: #fee2e2;
  padding: 8px 10px;
  border-radius: 8px;
}
</style>
