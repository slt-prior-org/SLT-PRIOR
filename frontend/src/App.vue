<template>
  <div>
    <!--This tells Vue to load the correct page based on the current URL-->
    <router-view /> 
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();

onMounted(() => {
  auth.fetchUser();
});
</script>