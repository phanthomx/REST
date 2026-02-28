<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../axios'

const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const success = ref('')

const handleRegister = async () => {
  error.value = ''
  success.value = ''

  try {
    // Send data to Flask
    await api.post('/register', { 
      username: username.value, 
      password: password.value 
    })
    
    success.value = 'Account created! Redirecting to login...'
    
    // Wait 1 second then go to login
    setTimeout(() => {
      router.push('/login')
    }, 1500)
    
  } catch (err) {
    // Handle errors (like username already exists)
    error.value = err.response?.data?.message || 'Registration failed'
  }
}
</script>

<template>
  <div style="max-width: 400px; margin: 50px auto; padding: 20px; border: 1px solid #ccc; border-radius: 8px;">
    <h1>Register</h1>
    
    <input 
      v-model="username" 
      placeholder="Username" 
      style="width: 100%; padding: 10px; margin-bottom: 10px;" 
    />
    
    <input 
      v-model="password" 
      type="password" 
      placeholder="Password" 
      style="width: 100%; padding: 10px; margin-bottom: 10px;" 
    />
    
    <button 
      @click="handleRegister" 
      style="width: 100%; padding: 10px; background: #42b983; color: white; border: none; border-radius: 4px; cursor: pointer;"
    >
      Register
    </button>

    <p v-if="error" style="color: red; margin-top: 10px;">{{ error }}</p>
    <p v-if="success" style="color: green; margin-top: 10px;">{{ success }}</p>
    
    <div style="margin-top: 15px;">
      Already have an account? <router-link to="/login">Login here</router-link>
    </div>
  </div>
</template>