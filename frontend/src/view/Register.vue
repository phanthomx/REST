<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../axios'

const router = useRouter()
const email = ref('')
const name = ref('')
const password = ref('')
const userType = ref('patient')
// Type-specific fields
const specialization = ref('')  // For doctors
const contactInfo = ref('')     // For patients
const cycleStage = ref('Onboarding')  // For patients

const error = ref('')

const handleRegister = async () => {
  error.value = ''
  
  const payload = {
    email: email.value,
    name: name.value,
    password: password.value,
    type: userType.value
  }
  
  // Add type-specific fields
  if (userType.value === 'doctor') {
    payload.specialization = specialization.value
    payload.license_number = 'DOC-' + Date.now()  // Simplified
  }
  if (userType.value === 'patient') {
    payload.contact_info = contactInfo.value
    payload.cycle_stage = cycleStage.value
  }
  
  try {
    const res = await api.post('/register', payload)
    router.push('/login')
  } catch (err) {
    error.value = err.response?.data?.message || 'Registration failed'
  }
}
</script>

<template>
  <div>
    <h1>Register</h1>
    
    <input v-model="email" placeholder="Email" type="email" required />
    <input v-model="name" placeholder="Full Name" required />
    <input v-model="password" placeholder="Password" type="password" required />
    
    <!-- User Type Selector -->
    <select v-model="userType">
      <option value="patient">Patient</option>
      <option value="doctor">Doctor</option>
      <option value="receptionist">Receptionist</option>
      <option value="accountant">Accountant</option>
      <option value="admin">Admin</option>
    </select>
    
    <!-- Doctor-specific fields -->
    <div v-if="userType === 'doctor'">
      <input v-model="specialization" placeholder="Specialization" />
    </div>
    
    <!-- Patient-specific fields -->
    <div v-if="userType === 'patient'">
      <input v-model="contactInfo" placeholder="Contact Info" />
      <select v-model="cycleStage">
        <option>Onboarding</option>
        <option>Baseline</option>
        <option>Stimulation</option>
        <option>Monitoring</option>
        <option>Trigger</option>
        <option>Retrieval</option>
        <option>Transfer</option>
      </select>
    </div>
    
    <button @click="handleRegister">Register</button>
    <p v-if="error" style="color:red">{{ error }}</p>
    
    <router-link to="/login">Already have an account? Login</router-link>
  </div>
</template>