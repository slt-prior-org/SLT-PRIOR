<template>
  <div class="chat-history-overlay" @click="closeSidebar">
    <div class="chat-history-sidebar" @click.stop>

      <div class="sidebar-header">
        <h3>{{$t('sidebar.pastChats')}}</h3>
        <button class="close-btn" @click="closeSidebar">✕</button>
      </div>

      <button class="new-chat-btn" @click="startNewChat">
        <span class="plus-icon">+</span> {{$t('sidebar.newChat')}}
      </button>

      <div class="chats-container" ref="chatsContainer">
        <ul v-if="groupedChats.length > 0" class="chats-list">
          <li
            v-for="chat in groupedChats"
            :key="chat.id"
            class="chat-item"
            :class="{ 'active-chat': chat.id === activeChatId }"
            @click="selectChatAndClose(chat)"
          >
            <span class="chat-title" :title="chat.lastMessage">
              {{ chat.lastMessage || $t('sidebar.defaultTitle') }}
            </span>
            <span class="chat-date">
              {{ formatDate(chat.lastMessageDate) }}
            </span>
          </li>
        </ul>
        <div v-else class="empty-state">
          {{$t('sidebar.noChats')}}
        </div>
      </div>

          <div class="sidebar-footer">
            {{$t('sidebar.footer')}}
          </div>

    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'

export default {
  name: 'ChatHistorySidebar',

  props: {
    chatHistory: {
      type: Array,
      required: true
    },
    activeChatId: {
      type: [String, Number],
      required: false
    }
  },

  setup(props) {
    const chatsContainer = ref(null)
    const scrollToTop = () => {
      if (chatsContainer.value) {
        chatsContainer.value.scrollTo({
          top: 0,
          behavior: 'smooth',
        })
      }
    }

    // Scroll to top when chat history is updated
    watch(
      () => props.chatHistory,
      () => {
        scrollToTop()
      },
      { deep: true }
    )

    return {
      chatsContainer,
      scrollToTop
    }
  },

  computed: {
    // Ryhmitellään ja järjestetään chatit, haetaan viimeisin käyttäjän viesti
    groupedChats() {
        return this.chatHistory
        .map(chat => {
            const messages = (chat.messages || []).sort(
            (a, b) => new Date(b.created_at) - new Date(a.created_at)
            )

            // Etsi viimeisin käyttäjän viesti
            const lastUserMsg = messages.find(m => m.sender === 'user')
            const messageText = lastUserMsg?.content || messages[0]?.content || this.$t('sidebar.defaultTitle')
            
            // Käytä viimeisin viestin aikaa tai chatin updated_at
            const lastMessageDate = messages[0]?.created_at || chat.updated_at || chat.created_at

            return {
            id: chat.id,
            lastMessage: messageText,
            lastMessageDate: lastMessageDate,
            }
        })
        .sort((a, b) => {
            return new Date(b.lastMessageDate) - new Date(a.lastMessageDate)
        })
    }
  },

  methods: {
    selectChat(chat) {
      this.$emit('select-chat', chat);
    },

    selectChatAndClose(chat) {
      this.selectChat(chat);
    },

    startNewChat() {
      this.$emit('start-new-chat');
    },

    closeSidebar() {
      this.$emit('close-sidebar');
    },

    // Päivämäärän muotoilu (tänään, eilen, muuten pvm)
    formatDate(dateString) {
      if (!dateString) return '';
      const correctedDateString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
      const date = new Date(correctedDateString);
      const today = new Date();
      const yesterday = new Date();
      yesterday.setDate(today.getDate() - 1);

      const dateLocal = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      const todayLocal = new Date(today.getFullYear(), today.getMonth(), today.getDate());
      const yesterdayLocal = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());

      if (dateLocal.getTime() === todayLocal.getTime()) {
        return date.toLocaleTimeString('fi-FI', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }

      if (dateLocal.getTime() === yesterdayLocal.getTime()) {
        return (
          this.$t('sidebar.yesterdayAt') +
          date.toLocaleTimeString('fi-FI', {
            hour: '2-digit',
            minute: '2-digit'
          })
        );
      }

      return date.toLocaleDateString('fi-FI', {
        day: 'numeric',
        month: 'short'
      });
    }
  }
};
</script>

<style scoped>
.chat-history-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1003;
  display: flex;
  animation: fadeIn 0.2s ease-in-out;
  pointer-events: none;
}

.chat-history-overlay.closing {
  animation: fadeOut 0.3s ease-in forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

.chat-history-sidebar {
  width: 280px;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
  pointer-events: auto;
}

@keyframes slideIn {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-100%);
  }
}

.chat-history-sidebar.closing {
  animation: slideOut 0.3s ease-in forwards;
}

.sidebar-header {
  position: relative;
  padding: 20px 0 0 20px;
  display: flex;
  align-items: center;
  min-height: 56px;
}

.sidebar-header h3 {
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  flex: 1;
}

.close-btn {
  position: absolute;
  right: 16px;
  top: 16px;
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
  z-index: 2;
}

.close-btn:hover {
  background: #e3e8f3;
}

.close-btn:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 1px;
}

.new-chat-btn {
  margin: 0 20px 20px 20px;
  padding: 14px 0;
  width: calc(100% - 40px);
  background: #1264a3;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(18, 100, 163, 0.2);
  transition: all 0.2s ease;
  outline: none;
}

.new-chat-btn:hover {
  background: #0f5791;
  box-shadow: 0 4px 12px rgba(18, 100, 163, 0.3);
}

.new-chat-btn:active {
  background: #0d4570;
}

.new-chat-btn:focus-visible {
  outline: 2px solid #1264a3;
  outline-offset: 2px;
}

.plus-icon {
  font-size: 20px;
  font-weight: 700;
  margin-right: 4px;
}

.login-card {
  background: #f1f6fe;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  margin: 0 20px 20px 20px;
  padding: 18px 18px 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.login-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.login-icon {
  font-size: 18px;
  color: #2563eb;
  font-weight: 700;
}

.login-title {
  font-size: 15px;
  font-weight: 600;
}

.login-card-text {
  font-size: 14px;
  color: #334155;
  margin-left: 26px;
}

.sidebar-footer {
  margin: 0 0 0 0;
  padding: 18px 20px 16px 20px;
  font-size: 14px;
  color: #2d445a;
  text-align: left;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
}

.chats-container {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 8px;
}

.chats-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.chat-item {
  padding: 12px 12px;
  margin-bottom: 4px;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s, border-left-color 0.2s;
  border-left: 3px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chat-item:hover {
  background: #f1f5f9;
  border-left-color: #1264a3;
}

.chat-item.active-chat {
  background: #dbeafe;
  border-left-color: #1264a3;
}

.chat-title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
  line-height: 1.3;
}

.chat-date {
  display: block;
  font-size: 12px;
  color: #94a3b8;
}

.empty-state {
  padding: 32px 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}

@media (max-width: 768px) {
  .chat-history-overlay {
    background-color: rgba(0, 0, 0, 0.4);
    pointer-events: auto;
    cursor: pointer;
  }

  .chat-history-sidebar {
    width: 100%;
    max-width: 320px;
  }
}

@media (max-width: 480px) {
  .chat-history-sidebar {
    width: 100%;
    max-width: 100%;
  }

  .sidebar-header {
    padding: 16px 0 0 16px;
  }

  .new-chat-btn {
    margin: 0 16px 16px 16px;
    width: calc(100% - 32px);
  }

  .chats-container {
    padding: 4px;
  }
}
</style>