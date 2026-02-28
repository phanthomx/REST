<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../axios'

const router = useRouter()
const username = ref('testuser')
const password = ref('test123')
const error = ref('')

const handleLogin = async () => {
  try {
    const res = await api.post('/login', { username: username.value, password: password.value })
    localStorage.setItem('token', res.data.token) // SAVE TOKEN
    router.push('/dashboard')
  } catch (err) {
    error.value = 'Login failed'
  }
}
</script>

<template>
  <div>
    <h1>Login</h1>
    <input v-model="username" placeholder="Username" />
    <input v-model="password" type="password" placeholder="Password" />
    <button @click="handleLogin">Login</button>
    <p v-if="error" style="color:red">{{ error }}</p>
    <router-link to="/register">Need an account?</router-link>
  </div>
</template>

const handleLogin = async () => {
  error.value = ''
  
  try {
    console.log('Attempting login with:', { username: username.value }) // DEBUG 1
    
    const res = await api.post('/login', { 
      username: username.value, 
      password: password.value 
    })
    
    console.log('Login SUCCESS response:', res.data) // DEBUG 2
    
    // Check if token exists in response
    if (res.data.token) {
      console.log('Saving token:', res.data.token) // DEBUG 3
      localStorage.setItem('token', res.data.token)
      router.push('/dashboard')
    } else {
      console.error('No token in response!', res.data) // DEBUG 4
      error.value = 'Login failed: No token received'
    }
    
  } catch (err) {
    console.error('Login ERROR:', err) // DEBUG 5
    console.error('Error details:', err.response?.data) // DEBUG 6
    error.value = err.response?.data?.message || 'Login failed'
  }
}