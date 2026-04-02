import axios from "axios"

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000"

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

api.interceptors.response.use(
  res => res.data,
  err => {
    console.error("[API Error]", err.message)
    return Promise.reject(err)
  }
)

export default api
