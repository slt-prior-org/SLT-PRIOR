/**
 * - Manages the raw WebSocket connection
 * - Reads token from sessionStorage
 * - Reconnects automatically on disconnect
 * - Calls a provided onMessage callback on events
 * - Exposes connect() and disconnect()
 */
class professionalQueueSocketManager {
    socket = null
    shouldReconnect = true
    
    connect(onMessage) {
        const token = sessionStorage.getItem("token")
        this.shouldReconnect = true

        this.socket = new WebSocket(
            `ws://127.0.0.1:8000/ws/professional/queue?token=${token}`
        )

        this.socket.onopen = () => {
            console.log("Professional queue websocket connected")
        }

        // onmessage
        this.socket.onmessage = (event) => {
            console.log("Received message from queue websocket:", event.data)
            const data = JSON.parse(event.data)
            onMessage(data)
        }

        // onerror
        this.socket.onerror = (error) => {
            console.error("Websocket error:", error)
        }

        // onclose
        this.socket.onclose = () => {
            console.log("Queue websocket closed")
            this.socket = null
            if(this.shouldReconnect){
                setTimeout(() => this.connect(onMessage), 3000)
            }
        }
    }

    // disconnect
    disconnect() {
        if (!this.socket) return
        this.shouldReconnect = false
        this.socket.close()
        this.socket = null
    }
}

export const professionalQueueSocket = new professionalQueueSocketManager()