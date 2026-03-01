<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../axios'

const router = useRouter()
const email = ref('')  // Changed from username
const password = ref('')
const error = ref('')

const handleLogin = async () => {
  error.value = ''
  
  try {
    const res = await api.post('/login', {
      email: email.value,  // Send email, not username
      password: password.value
    })
    
    // Save token AND user info
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    
    router.push('/dashboard')
    
  } catch (err) {
    error.value = err.response?.data?.message || 'Login failed'
  }
}
</script>

<template>
  <div>
    <h1>Login</h1>
    <input v-model="email" placeholder="Email" type="email" />
    <input v-model="password" placeholder="Password" type="password" />
    <button @click="handleLogin">Login</button>
    <p v-if="error" style="color:red">{{ error }}</p>
    <router-link to="/register">Need an account? Register</router-link>
  </div>
</template>