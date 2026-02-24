import { api } from "./api"

export const fetchAllUserChats = async () => {
  const response = await api.get("/api/chat")
  return response.data
}

export const fetchChat = async (chatId) => {
  const response = await api.get(`/api/chat/${chatId}`)
  return response.data
}

export const sendUserMessage = async (chatId, message) => {
  const response = await api.post(`/api/chat/${chatId}`, message)
  return response.data
}

export const addChat = async () => {
  const response = await api.post("/api/chat")
  return response.data
}