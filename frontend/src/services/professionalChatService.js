import { api } from "./api";

export const fetchChat = async (chatId) => {
    const response = await api.get(`/api/professional/chats/${chatId}`)
    return response.data
}

export const addProfessionalMessage = async (chatId, message) => {
    const response = await api.post(`/api/professional/chats/${chatId}/messages`, message)
    return response.data
}

export const claim = async (chatId) => {
    const response = await api.post(`/api/professional/chats/${chatId}/claim`)
    return response.data
}

export const close = async (chatId) => {
    const response = await api.post(`/api/professional/chats/${chatId}/close`)
    return response.data
}

export const fetchQueues = async () => {
    const response = await api.get("/api/professional/chats/queue")
    return response.data
}