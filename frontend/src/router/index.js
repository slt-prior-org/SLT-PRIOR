import { createRouter, createWebHistory } from "vue-router";
import ChatView from "@/views/ChatView.vue"; 
import ProfessionalView from "@/views/ProfessionalView.vue";
import ProfessionalChatView from "@/views/ProfessionalChatView.vue";


// Sivujen reitit ja niihin liittyvät roolit/metatiedot
const routes = [
  {
    path: "/",
    component: ChatView,
    meta: { allowedRoles: ["patient"] } // Vain potilaille
  },
  {
    path: "/professional",
    component: ProfessionalView,
    meta: { requiresAuth: true, allowedRoles: ["professional"] } // Vain ammattilaisille, vaatii kirjautumisen
  },
  {
    path: "/professional/chat/:id",
    component: ProfessionalChatView,
    meta: { requiresAuth: true, allowedRoles: ["professional"] } // Ammattilaisen chat-näkymä
  }
];


const router = createRouter({
  history: createWebHistory(), // Enables modern browser history mode
  routes
});


// Tuodaan authStore navigaatiovartijaa varten
import { useAuthStore } from "@/stores/authStore";


// Navigaatiovartija ohjaa käyttäjiä roolin ja kirjautumistilan mukaan
router.beforeEach((to, from, next) => {
  const auth = useAuthStore();
  const userRole = auth.user?.role; // 'professional', 'patient' tai undefined
  const isAuthenticated = auth.isAuthenticated;
  const allowedRoles = to.meta.allowedRoles;

  // Määritellään oletussivut rooleittain
  const roleHome = {
    professional: '/professional',
    patient: '/',
  };

  // Selvitetään mihin käyttäjän kuuluisi päätyä
  const userHome = isAuthenticated ? (roleHome[userRole] || '/') : '/';

  // Jos sivu vaatii kirjautumisen, mutta käyttäjä ei ole kirjautunut
  if (to.meta.requiresAuth && !isAuthenticated) {
    return next('/');
  }

  // Tarkistetaan onko käyttäjän roolilla pääsy tälle sivulle
  if (allowedRoles && !allowedRoles.includes(userRole)) {
    // Jos käyttäjä on jo oikealla "kotisivullaan", päästetään läpi
    if (to.path === userHome) {
      return next();
    }
    // Muuten palautetaan käyttäjä hänen omalle sivulleen
    return next(userHome);
  }

  // 5. Jos mikään ehto ei täyty, jatketaan normaalisti
  next();
});

export default router;
