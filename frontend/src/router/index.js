import { createRouter, createWebHistory } from "vue-router";
import ChatView from "@/views/ChatView.vue"; 
import ProfessionalView from "@/views/ProfessionalView.vue";
import ProfessionalChatView from "@/views/ProfessionalChatView.vue";

// Available pages
const routes = [
  { path: "/", component: ChatView },
  { path: "/professional", component: ProfessionalView },
  { path: "/professional/chat/:id", component: ProfessionalChatView }
];

const router = createRouter({
  history: createWebHistory(), // Enables modern browser history mode
  routes
});

export default router;
