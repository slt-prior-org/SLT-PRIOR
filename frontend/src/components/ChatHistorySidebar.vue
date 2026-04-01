<template>
  <div class="chat-history-overlay">
    <div class="chat-history-sidebar">

      <!-- Sivupalkin otsikko ja sulje-painike -->
      <div class="sidebar-header">
        <h3>{{$t('sidebar.pastChats')}}</h3>
        <button class="close-btn" @click="closeSidebar">X</button>
      </div>

      <!-- Uusi keskustelu -painike -->
      <button class="new-chat-btn" @click="startNewChat">
        <span class="plus-icon">+</span> {{$t('sidebar.newChat')}}
      </button>

      <!-- Chat-historian lista -->
      <div class="chats-container">
        <ul v-if="groupedChats.length > 0" class="chats-list">
          <li
            v-for="chat in groupedChats"
            :key="chat.id"
            class="chat-item"
            @click="selectChatAndClose(chat)"
          >
            <span class="chat-title" :title="chat.lastMessage">
              {{ chat.lastMessage || $t('sidebar.defaultTitle') }}
            </span>
            <span class="chat-date">
              {{ formatDate(chat.created_at) }}
            </span>
          </li>
        </ul>
        <div v-else class="empty-state">
          {{$t('sidebar.noChats')}}
        </div>
      </div>

      <!-- Sivupalkin alatunniste -->
      <div class="sidebar-footer">
        {{$t('sidebar.footer')}}
      </div>

    </div>
  </div>
</template>

<script>
// Chat-historiasivupalkin päälogiikka
export default {
  name: 'ChatHistorySidebar',

  // Chat-historia prop
  props: {
    chatHistory: {
      type: Array,
      required: true
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

            return {
            id: chat.id,
            lastMessage: messageText,
            created_at: chat.created_at || messages[0]?.created_at,
            }
        })
        .sort((a, b) => {
            return new Date(b.created_at) - new Date(a.created_at)
        })
    }
  },

  methods: {
    // Emitoi valitun chatin vanhemmalle
    selectChat(chat) {
      this.$emit('select-chat', chat);
    },

    // Valitse chat ja sulje sivupalkki
    selectChatAndClose(chat) {
      this.selectChat(chat);
    },

    // Aloita uusi keskustelu
    startNewChat() {
      this.$emit('start-new-chat');
    },

    // Sulje sivupalkki
    closeSidebar() {
      this.$emit('close-sidebar');
    },

    // Päivämäärän muotoilu (tänään, eilen, muuten pvm)
    formatDate(dateString) {
      if (!dateString) return '';

      const date = new Date(dateString);
      const today = new Date();
      const yesterday = new Date();
      yesterday.setDate(today.getDate() - 1);

      if (date.toDateString() === today.toDateString()) {
        return date.toLocaleTimeString('fi-FI', {
          hour: '2-digit',
          minute: '2-digit'
        });
      }

      if (date.toDateString() === yesterday.toDateString()) {
        return 'Eilen';
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
  padding: 20px 0 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.sidebar-header h3 {
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  flex: 1;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #64748b;
  padding: 0 20px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
  flex-shrink: 0;
}

.close-btn:hover {
  color: #0f172a;
}

.new-chat-btn {
  margin: 0 20px 20px 20px;
  padding: 14px 0;
  width: calc(100% - 40px);
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 16px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  box-shadow: 0 2px 8px rgba(37,99,235,0.08);
  transition: background 0.2s;
}

.new-chat-btn:hover {
  background: #1d4ed8;
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
  color: #64748b;
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
  border-left-color: #1d4ed8;
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
</style>