import { createApp } from 'vue'
import App from './App.vue'
import router from "./router";
import i18n from "./i18n"; // i18n-konfiguraatio kielenvaihdosta varten
import { library } from "@fortawesome/fontawesome-svg-core";
import { faBars, faTimes } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import "@/assets/styles.css";
import { createPinia } from "pinia";
import piniaPersist from "pinia-plugin-persistedstate"
import { useAuthStore } from "@/stores/authStore"


library.add(faBars, faTimes);

const app = createApp(App);
const pinia = createPinia();
pinia.use(piniaPersist)

app.component("FontAwesomeIcon", FontAwesomeIcon); // Register globally
app.use(i18n);
app.use(pinia); 
app.use(router);

const auth = useAuthStore()

if(auth.token) {
    auth.fetchUser()
}

app.mount('#app')