class ChatSocketManager {
  socket = null
  chatId = null

  connect(chatId, token, onMessage) {
    if (this.socket && this.chatId === chatId) return

    if (this.socket) {
      this.disconnect()
    }

    this.chatId = chatId

    this.socket = new WebSocket(
      `ws://localhost:8000/ws/chats/${chatId}?token=${token}`
    )

    this.socket.onopen = () => {
      console.log("Chat websocket connected")
    }

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === "chat_closed") {
        console.log("Chat websocket closed by server")
        this.socket.close()
      } else {
        onMessage(data)
      }
    }

    this.socket.onerror = (error) => {
      console.error("WebSocket error:", error)
    }

    this.socket.onclose = () => {
      console.log("Chat websocket closed")
      this.socket = null
      this.chatId = null
    }
  }

  disconnect() {
    if (!this.socket) return

    this.socket.close()
    this.socket = null
    this.chatId = null
  }

  send(data) {
    if (!this.socket) return
    this.socket.send(JSON.stringify(data))
  }
}

export const chatSocket = new ChatSocketManager()