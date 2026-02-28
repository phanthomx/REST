<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../axios'

const router = useRouter()
const message = ref('')

onMounted(async () => {
  try {
    const res = await api.get('/dashboard')
    message.value = res.data.message
  } catch (err) {
    // If token is invalid/expired
    localStorage.removeItem('token')
    router.push('/login')
  }
})

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<template>
  <div>
    <h1>Dashboard</h1>
    <p>{{ message }}</p>
    <button @click="logout">Logout</button>
  </div>
</template>