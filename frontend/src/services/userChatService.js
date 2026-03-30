// Käyttäjän chat-palvelut: API-kutsut backendille
import { api } from "./api"

export const fetchAllUserChats = async () => {
  const response = await api.get("/api/chat") // Hakee kaikki chatit
  return response.data
}

export const fetchChat = async (chatId) => {
  const response = await api.get(`/api/chat/${chatId}`) // Hakee yksittäisen chatin
  return response.data
}

export const sendUserMessage = async (chatId, message) => {
  const response = await api.post(`/api/chat/${chatId}`, { message })
  return response.data
}

export const addChat = async () => {
  const response = await api.post("/api/chat/chat") // Luo uuden chatin
  return response.data
}

export const updateChatStatus = (chatId, status) =>
  api.put(`/api/chat/${chatId}/status`, { status })
