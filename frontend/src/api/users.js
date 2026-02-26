import axios from "axios";

const API_URL = "http://127.0.0.1:8000";  // FastAPI backend URL

export const createUser = async (userData) => {
  try {
    const response = await axios.post(`${API_URL}/api/users/`, userData);
    console.log("✅ User created:", response.data);
    return response.data.user_id;  // Return user ID to the frontend
  } catch (error) {
    console.error("❌ Error creating user:", error.response?.data || error.message);
    return null;
  }
};

export const registerUser = async (userData) => {
  try {
    const response = await axios.post(`${API_URL}/users/register`, userData);
    console.log("✅ User created:", response.data);
    return response.data.user_id;  // Return user ID to the frontend
  } catch (error) {
    console.error("❌ Error creating user:", error.response?.data || error.message);
    return null;
  }
};


/*export const getUser = async (patientId) => {
  try {
    const response = await axios.get(`${API_URL}/users/${patientId}`);
    console.log("✅ User data received:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching user:", error.response?.data || error.message);
     
    if (error.response?.data?.detail) {
      console.error("⚠️ Validation Errors:", error.response.data.detail);
    }
    return null;
  }
};*/

/*export const updateUser = async (patientId, userData) => {
  try {
    const response = await axios.put(`${API_URL}/users/${patientId}`, userData);
    console.log("✅ User updated:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Error updating user:", error.response?.data || error.message);
    return null;
  }
};*/

/*export const deleteUser = async (patientId) => {
  try {
    const response = await axios.delete(`${API_URL}/users/${patientId}`);
    console.log("✅ User deleted:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Error deleting user:", error.response?.data || error.message);
    return null;
  }
};*/
