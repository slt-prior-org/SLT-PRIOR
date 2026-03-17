import { createI18n } from "vue-i18n";
import fi from "./locales/fi.json";
import en from "./locales/en.json";

const savedLanguage = localStorage.getItem("selectedLanguage") || "fi";

const i18n = createI18n({
  legacy: false, // Composition API mode
  locale: savedLanguage,
  fallbackLocale: "fi",
  messages: { fi, en },
});

export default i18n;