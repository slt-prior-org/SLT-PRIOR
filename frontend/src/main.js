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
    auth.fetchUser().then(() => {
        // Ohjataan tallennettuun reittiin, jos käyttäjä on ammattilainen tai potilas ja reitti on tallennettu
        const professionalRoute = sessionStorage.getItem('professional-last-route');
        const patientRoute = sessionStorage.getItem('patient-last-route');
        if (auth.user?.role === 'professional' && professionalRoute && window.location.pathname !== professionalRoute) {
            router.replace(professionalRoute);
        } else if (auth.user?.role === 'patient' && patientRoute && window.location.pathname !== patientRoute) {
            router.replace(patientRoute);
        }
        app.mount('#app')
    });
} else {
    app.mount('#app')
}