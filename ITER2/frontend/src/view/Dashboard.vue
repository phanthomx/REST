<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../axios'

const router = useRouter()
const message = ref('')
const user = ref(null)
const dashboardData = ref(null)

onMounted(async () => {
  try {
    const res = await api.get('/dashboard')
    message.value = res.data.message
    user.value = res.data.user
    dashboardData.value = res.data.dashboard_data
  } catch (err) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
})

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<template>
  <div>
    <h1>Dashboard</h1>
    <p>{{ message }}</p>
    
    <div v-if="user">
      <p><strong>Name:</strong> {{ user.name }}</p>
      <p><strong>Email:</strong> {{ user.email }}</p>
      <p><strong>Type:</strong> {{ user.type }}</p>
      <p><strong>Roles:</strong> {{ user.roles?.join(', ') }}</p>
      
      <!-- Patient-specific -->
      <div v-if="user.type === 'patient'">
        <p><strong>Service ID:</strong> {{ user.service_id }}</p>
        <p><strong>IVF Stage:</strong> {{ dashboardData?.cycle_stage }}</p>
      </div>
      
      <!-- Doctor-specific -->
      <div v-if="user.type === 'doctor'">
        <p><strong>Specialization:</strong> {{ dashboardData?.specialization }}</p>
        <p><strong>Today's Appointments:</strong> {{ dashboardData?.today_appointments }}</p>
      </div>
      
      <!-- Admin-specific -->
      <div v-if="user.roles?.includes('admin')">
        <h3>Admin Controls</h3>
        <p>Total Users: {{ dashboardData?.total_users }}</p>
        <button @click="router.push('/admin/users')">Manage Users</button>
      </div>
    </div>
    
    <button @click="logout">Logout</button>
  </div>
</template>