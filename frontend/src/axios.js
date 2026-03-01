import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    // ⚠️ MUST be "Bearer <token>" with a space!
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api