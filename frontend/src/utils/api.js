/**
 * BLARE API client.
 * All backend calls go through this axios instance.
 */
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

api.interceptors.response.use(
  res => res.data,
  err => {
    console.error('[BLARE API Error]', err.message)
    return Promise.reject(err)
  }
)

export default api
