import { api } from "./api"

export const registerUser = async (data) => {
  const response = await api.post("/api/auth/register", data)
  return response.data
}

export const loginUser = async (email, password) => {
  const response = await api.post("/api/auth/login", { email, password })
  return response.data
}

export const logoutUser = async () => {
  const response = await api.post("/api/auth/logout")
  return response.data
}

export const updateUserProfile = async (data, token) => {
  const response = await api.put("/api/auth/me", data, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
}

export const fetchUser = async (token) => {
  const response = await api.get("/api/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data
}
